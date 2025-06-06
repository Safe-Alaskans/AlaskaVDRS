import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, TypeVar, Type, Optional
from uuid import uuid4

from model_tuning_workspace.synthetic_data_pipeline.framework.feature import TopLevelFeature

_TopLevelFeatureType = TypeVar('_TopLevelFeatureType', bound=TopLevelFeature)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineContext:
    """Maintains state and data flow between pipeline steps"""

    def __init__(
            self,
            pipeline_run_id: str,
            iteration_id: int,
    ):
        self.pipeline_run_uuid: str = pipeline_run_id
        self.iteration_id: int = iteration_id
        self.features: Dict[str, TopLevelFeature] = {}
        self.intermediate_outputs: Dict[str, Any] = {}

    def add_feature(self, feature: TopLevelFeature) -> None:
        self.features[feature.name] = feature

    def get_feature(self, name: str, feature_type: Type[_TopLevelFeatureType]) -> _TopLevelFeatureType:
        ft = self.features[name]
        if not isinstance(ft, feature_type):
            raise ValueError(f"Feature {name} is not of type {feature_type.__name__}")
        return ft

    def set_output(self, step_name: str, output: Any) -> None:
        self.intermediate_outputs[step_name] = output

    def get_output(self, step_name: str) -> Any:
        return self.intermediate_outputs.get(step_name)


class PipelineStep(ABC):
    def __init__(self, step_name: str):
        self.step_name = step_name

    @abstractmethod
    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        pass


class Pipeline:
    def __init__(self, steps: List[PipelineStep]):
        self.run_id = str(uuid4())
        self.steps = steps
        self.context: Optional[PipelineContext] = None

    def execute(
            self,
            iteration_number: int,
    ) -> List[str]:
        logger.info(f"Starting pipeline run {self.run_id}")
        self.context = PipelineContext(
            pipeline_run_id=self.run_id,
            iteration_id=iteration_number,
        )
        outputs = []
        for step in self.steps:
            logger.info(f"Executing step {step.step_name}")
            output, was_success = step.execute(self.context)
            logger.info(f"Step {step.step_name} executed successfully: {was_success}")
            if not was_success:
                outputs.append(f"Error in {step.step_name}: {output}")
                break
            outputs.append(f"{step.step_name}: {output}")

        logger.info(f"Pipeline run {self.run_id} completed")
        return outputs
