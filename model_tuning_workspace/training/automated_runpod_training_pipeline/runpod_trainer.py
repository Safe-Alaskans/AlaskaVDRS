import subprocess

import runpod
import time
import logging
from pathlib import Path
from typing import Optional

from model_tuning_workspace.training.automated_runpod_training_pipeline.utils import get_port_mappings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RunPodTrainer:
    def __init__(
            self,
            runpod_api_key: str,
            hf_token: str,
            path_to_dataset: str,
            model_to_ft: str,
            model_name: str,
            new_model_version: float,
            training_script_path: str,
            gpu_id: str,
            container_disk_size_gb: int = 50,
            num_gpus: int = 1,
            max_seq_length: int = 1000,
    ):
        runpod.api_key = runpod_api_key
        self.hf_token = hf_token
        self.dataset_path = Path(path_to_dataset)
        self.model_to_ft = model_to_ft
        self.model_name = model_name
        self.model_version = new_model_version
        self.training_script_path = Path(training_script_path)
        self.gpu_id = gpu_id
        self.container_disk_size_gb = container_disk_size_gb
        self.num_gpus = num_gpus
        self.max_seq_length = max_seq_length

        self.remote_workspace = "/workspace"
        self.remote_script_path = f"{self.remote_workspace}/{self.training_script_path.name}"
        self.remote_dataset_path = f"{self.remote_workspace}/{self.dataset_path.name}"

        self.pod_id: Optional[str] = None
        self.pod_public_ip: Optional[str] = None
        self.ssl_port: Optional[int] = None
        self.http_port: Optional[int] = None



    def setup_training_environment(self):
        """Create and configure the pod with necessary environment"""
        try:
            logger.info("Creating RunPod instance...")
            pod_stat = runpod.create_pod(
                name=f"train-{self.model_name}-v{self.model_version}",
                image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
                container_disk_in_gb=self.container_disk_size_gb,
                gpu_count=self.num_gpus,
                gpu_type_id=self.gpu_id,
                ports="22/tcp,9000/tcp",
                support_public_ip=True,
                env={
                    "HF_TOKEN": self.hf_token,
                },
                min_download=1000,
            )
            self.pod_id = pod_stat["id"]
            logger.info(f"Created pod with ID: {self.pod_id}")

            # Wait for pod to be ready
            pod_stat = self._wait_for_pod_ready()
            if not pod_stat:
                self.cleanup()
                return False

            if not self._transfer_file_to_pod(self.training_script_path):
                self.cleanup()
                return False

            if not self._transfer_file_to_pod(self.dataset_path):
                self.cleanup()
                return False

            logger.info("Training environment setup complete")
            return True
        except Exception as e:
            logger.error(f"Failed to setup training environment: {str(e)}")
            self.cleanup()
            return False


    def _wait_for_pod_ready(self) -> Optional[dict]:
        """Wait for pod to be in ready state"""
        count = 0
        logger.info("Waiting for pod to be ready...")
        time.sleep(15)
        while count < 18: # Wait for a further 90 seconds
            pod_stat = runpod.get_pod(self.pod_id)
            if pod_stat["runtime"] and pod_stat["runtime"]["ports"]:
                print(pod_stat["runtime"]["ports"])
                port_mappings = get_port_mappings(pod_stat)
                if not port_mappings:
                    logger.info("No port mappings found")
                    count += 1
                    time.sleep(5)
                    continue
                self.pod_public_ip = port_mappings["ssh"]["ip"]
                self.ssl_port = port_mappings["ssh"]["port"]
                self.http_port = port_mappings["http"]["port"]
                logger.info("Pod is ready")
                return pod_stat
            logger.info(f"Still waiting for pod to be ready... ({count + 1}/18)")
            count += 1
            time.sleep(5)

        logger.error("Pod did not become ready")
        return None



    def _transfer_file_to_pod(self, local_path: Path, remote_dir: str = "/workspace/") -> bool:
        """
        Transfer a file to the pod using scp
        Args:
            local_path: Path to the local file to transfer
            remote_dir: Directory on the pod where the file should be transferred to
        Returns:
            bool: True if successful, False otherwise
        """
        if not all([self.pod_public_ip, self.ssl_port]):
            logger.error("Missing pod connection information")
            return False

        if not local_path.exists():
            logger.error(f"Local file {local_path} does not exist")
            return False

        try:
            # Use the preconfigured remote path based on the file type
            if local_path == self.training_script_path:
                remote_path = self.remote_script_path
            elif local_path == self.dataset_path:
                remote_path = self.remote_dataset_path
            else:
                remote_path = f"{remote_dir.rstrip('/')}/{local_path.name}"

            # Construct the scp command
            scp_command = [
                "scp",
                "-P", str(self.ssl_port),
                "-o", "StrictHostKeyChecking=no",
                str(local_path),
                f"root@{self.pod_public_ip}:{remote_path}"
            ]

            logger.info(f"Transferring {local_path} to pod at {remote_path}...")
            result = subprocess.run(
                scp_command,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"SCP transfer failed: {result.stderr}")
                return False

            logger.info(f"File {local_path.name} transferred successfully to {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to transfer file {local_path}: {str(e)}")
            return False

    def _run_ssh_command(self, command: str, stream_output: bool = False) -> tuple[bool, str]:
        """
        Execute a command on the pod via SSH
        Args:
            command: Command to execute
            stream_output: Whether to stream output in real-time
        Returns:
            tuple: (success bool, command output)
        """
        if not all([self.pod_public_ip, self.ssl_port]):
            logger.error("Missing pod connection information")
            return False, ""

        ssh_command = [
            "ssh",
            "-p", str(self.ssl_port),
            "-o", "StrictHostKeyChecking=no",
            "-tt" if stream_output else "",
            f"root@{self.pod_public_ip}",
            command
        ]
        # Remove empty strings from command
        ssh_command = [arg for arg in ssh_command if arg]

        try:
            if not stream_output:
                result = subprocess.run(
                    ssh_command,
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0, result.stdout

            # Execute command and stream output
            process = subprocess.Popen(
                ssh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Handle output streams in parallel
            def stream_handler(stream, is_error=False):
                while True:
                    line = stream.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        if is_error:
                            logger.error(f"SSH error: {line.rstrip()}")
                        else:
                            logger.info(f"SSH output: {line.rstrip()}")

            from threading import Thread
            stdout_thread = Thread(target=stream_handler, args=(process.stdout,))
            stderr_thread = Thread(target=stream_handler, args=(process.stderr, True))

            stdout_thread.start()
            stderr_thread.start()

            # Wait for process to complete
            process.wait()

            # Wait for output processing to complete
            stdout_thread.join()
            stderr_thread.join()

            success = process.returncode == 0
            return success, ""
        except Exception as e:
            logger.error(f"Failed to execute SSH command: {str(e)}")
            return False, str(e)


    def run_training(self) -> bool:
        """Main method to run the training process"""
        try:
            # Install requirements
            if not self.install_requirements():
                return False

            # Execute training script
            if not self.execute_training_script():
                return False

            logger.info("Training process completed successfully")
            return True

        except Exception as e:
            logger.error(f"Training process failed: {str(e)}")
            return False
        finally:
            self.cleanup()

    def install_requirements(self) -> bool:
        """Install required packages on the pod"""
        logger.info("Installing requirements (This may take a few minutes)...")
        success, output = self._run_ssh_command("pip install unsloth", stream_output=True)
        if not success:
            logger.error("Failed to install unsloth")
            return False
        logger.info("Unsloth installed successfully")

        success, output = self._run_ssh_command("pip uninstall unsloth -y && pip install --upgrade --no-cache-dir --no-deps git+https://github.com/unslothai/unsloth.git", stream_output=True)
        if not success:
            logger.error("Failed to install unsloth nightly")
            return False
        logger.info("Unsloth nightly installed successfully")

        logger.info("All requirements installed successfully")
        return True

    def execute_training_script(self) -> bool:
        """Execute the training script with command line arguments"""
        logger.info("Starting training script execution...")

        # Build command line arguments string
        args_str = (
            f"--model_name {self.model_name} "
            f"--model_version {self.model_version} "
            f"--model_to_ft {self.model_to_ft} "
            f"--dataset_path {self.remote_dataset_path} "
            f"--max_seq_length {self.max_seq_length} "
            f"--hf_token {self.hf_token}"
        )

        success, _ = self._run_ssh_command(
            f"python -u {self.remote_script_path} {args_str}",
            stream_output=True
        )

        if not success:
            logger.error("Training script execution failed")
            return False

        logger.info("Training script completed successfully")
        return True
    def cleanup(self):
        """Cleanup resources"""
        if self.pod_id:
            logger.info(f"Terminating pod {self.pod_id}")
            try:
                runpod.terminate_pod(self.pod_id)
            except Exception as e:
                logger.error(f"Failed to terminate pod: {str(e)}")
