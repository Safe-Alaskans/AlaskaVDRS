import os
import logging
from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.validation import Validator, ValidationError
from file_processing import process_input, get_file_info
from local_extraction import master_script
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the style at the top level of the module
style = Style.from_dict({
    'welcome': '#ffffff bold',  # White, bold
    'prompt': '#00ffff',        # Cyan
    'input': '#ffffff',         # White
    'info': '#00ff00',          # Green
    'warning': '#ffff00',       # Yellow
    'error': '#ff0000',         # Red
    'arrow': '#ff00ff',         # Magenta
    'progress-bar': 'bg:#ansiblue',
    'progress-bar.used': 'bg:#ansiyellow',
    'label': 'bg:#ansiblue #ansiwhite',
    'percentage': 'bg:#ansiblue #ansiwhite',
    'bar-a': 'bg:#00ff00 #000000',
    'bar-b': 'bg:#00ff00 #000000',
    'bar-c': 'bg:#000000 #00ff00',
})

# Custom validators
class PathValidator(Validator):
    def validate(self, document):
        if not os.path.exists(document.text):
            raise ValidationError(message='Invalid path')
        

class WorkerValidator(Validator):
    def validate(self, document):
        try:
            value = int(document.text)
            if value < 1 or value > 3:
                raise ValidationError(message='Number of workers must be between 1 and 3')
        except ValueError:
            raise ValidationError(message='Please enter a valid number')

class YesNoValidator(Validator):
    def validate(self, document):
        text = document.text.lower()
        if text not in ['y', 'n', 'yes', 'no']:
            raise ValidationError(message='Please enter Y/N')

# Custom logging handler
class PromptToolkitLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        level_style = {
            'DEBUG': 'class:debug',
            'INFO': 'class:info',
            'WARNING': 'class:warning',
            'ERROR': 'class:error',
            'CRITICAL': 'class:error bold'
        }.get(record.levelname, 'class:info')
        print_formatted_text(FormattedText([(level_style, log_entry)]), style=style)

def styled_prompt(message, validator=None, default=''):
    print()  # Add a blank line before the prompt
    result = prompt(
        HTML(f'<arrow>➤</arrow> <prompt>{message}</prompt> '),
        style=style,
        validator=validator,
        default=default
    )
    return result

def confirm(message, default=None):
    if default is None:
        return styled_prompt(
            f"{message} (y/n): ",
            validator=YesNoValidator()
        ).lower().startswith('y')
    else:
        return styled_prompt(
            f"{message} (y/n): ",
            validator=YesNoValidator(),
            default=default
        ).lower().startswith('y')

def main():
    # Stylized welcome message
    print_formatted_text(HTML('''
<welcome>
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Welcome to Data2LLMBeta: A Work In Progress!         ║
║                                                          ║
║           Version 0.2.0 - September 2024                 ║
║                                                          ║
║    Transforming documents into LLM-ready datasets        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
</welcome>
    '''), style=style)

    use_local = confirm("Do you want to use local extraction?", default='n')
    if use_local:
        master_script.main()
    else:
        # Set up logging with custom handler
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(PromptToolkitLogHandler())

        # Remove all other handlers to avoid duplicate logging
        for handler in logger.handlers[:]:
            if not isinstance(handler, PromptToolkitLogHandler):
                logger.removeHandler(handler)

        # Disable propagation for all loggers
        logging.getLogger().propagate = False
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).propagate = False

        try:
            debug_mode = confirm("Do you want to enable debug mode?", default='n')
            if debug_mode:
                logger.setLevel(logging.DEBUG)
            
            input_path = styled_prompt(
                "Enter the path to the input file or directory:",
                validator=PathValidator()
            )

            # Get file information
            total_files, total_size = get_file_info(input_path)

            save_raw = confirm("Do you want to save the raw text?", default='n')
            chunked = confirm("Do you want to generate chunked JSON files?")  # No default
            output_suffix = styled_prompt("Enter a suffix for the output directory name:", default="")
            
            max_workers = int(styled_prompt(
                "Enter the number of worker threads (1-3):",
                validator=WorkerValidator(),
                default="1"
            ))

            # Confirm the user's choices
            print_formatted_text(HTML('\n<b>You\'ve selected the following options:</b>'))
            print_formatted_text(HTML(f"<info>Debug mode:</info> {'Enabled' if debug_mode else 'Disabled'}"))
            print_formatted_text(HTML(f"<info>Input path:</info> {input_path}"))
            print_formatted_text(HTML(f"<info>Save raw text:</info> {'Yes' if save_raw else 'No'}"))
            print_formatted_text(HTML(f"<info>Generate chunked JSON files:</info> {'Yes' if chunked else 'No'}"))
            print_formatted_text(HTML(f"<info>Output directory suffix:</info> {output_suffix if output_suffix else 'None'}"))
            print_formatted_text(HTML(f"<info>Number of worker threads:</info> {max_workers}"))
            print_formatted_text(HTML(f"<info>Number of supported files found:</info> {total_files}"))
            print_formatted_text(HTML(f"<info>Total size:</info> {total_size:.2f} MB"))

            if confirm("Do you want to proceed?"):  # No default
                with ProgressBar(style=style) as pb:
                    file_progress = pb(range(total_files), label='Processing files')
                    chunk_progress = pb(range(1), label='Processing chunks')  # Initialize with range(1)

                    def update_progress(current_file, total_files, current_chunk, total_chunks):
                        file_progress.items_completed = current_file - 1  # Subtract 1 to make it zero-based
                        file_progress.label = HTML(f'<ansiyellow>Processing files: {current_file}/{total_files}</ansiyellow>')
                        
                        if total_chunks > 0:
                            if chunk_progress.total != total_chunks:
                                chunk_progress.total = total_chunks
                            chunk_progress.items_completed = current_chunk - 1  # Subtract 1 to make it zero-based
                            chunk_progress.label = HTML(f'<ansigreen>Processing chunks: {current_chunk}/{total_chunks}</ansigreen>')
                        else:
                            chunk_progress.total = 1
                            chunk_progress.items_completed = 0
                            chunk_progress.label = HTML('<ansigreen>Single chunk processed</ansigreen>')

                    processed_files, total_tokens = process_input(input_path, save_raw, chunked, output_suffix, debug_mode, progress_callback=update_progress, max_workers=max_workers)

                print()  # Add a blank line for separation
                print_formatted_text(HTML(f"<ansicyan>Total number of input files processed:</ansicyan> {processed_files}"))
                print_formatted_text(HTML(f"<ansicyan>Total number of tokens used:</ansicyan> {total_tokens}"))
                logger.info("Processing complete.")
            else:
                logger.info("Operation cancelled.")

        except KeyboardInterrupt:
            logger.warning("\nOperation cancelled by user.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            logger.error("Please check the log for details.")

if __name__ == "__main__":
    main()