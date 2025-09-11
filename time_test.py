from core.config import BarcodeConfig, InputConfig, PreviewConfig, AggregationConfig
from line_profiler import profile
import traceback


def create_processing_worker(
    config: BarcodeConfig,
    input_config: InputConfig,
    aggregation_config: AggregationConfig,
):
    """Create the worker function for processing in background thread"""

    if input_config.configuration_file:
        try:
            config = BarcodeConfig.load_from_yaml(input_config.configuration_file)
        except Exception as e:
            print("Error reading config file", str(e))
            return

    try:
        mode = input_config.mode

        from core.pipeline import run_analysis

        # Handle file/directory processing
        file_path = input_config.file_path
        dir_path = input_config.dir_path

        if not (dir_path or file_path):
            print(
                "Error", "No file or directory has been selected."
            )
            return

        channels = config.channels.parse_all_channels
        channel_selection = config.channels.selected_channel
        if not (channels or (channel_selection is not None)):
            print("Error", "No channel has been specified.")
            return

        dir_name = dir_path if dir_path else file_path

        run_analysis(dir_name, config)

    except Exception as e:
        print(f"Error during processing: {e}")
        print(traceback.format_exc())
        print("Error during processing", str(e))

    finally:
        print(
            "Processing Complete", "Analysis has finished successfully."
        )

#@profile
def main():
    dirpath = "F:/Dataset 1/results/A-A + kinesin"
    mode = "dir"
    configuration_file = "F:/Dataset 1/results/A-A + kinesin/A-A + kinesin Settings.yaml"

    config_b = BarcodeConfig()
    config_i = InputConfig(
        dir_path = dirpath,
        mode = mode,
        configuration_file = configuration_file
    )
    config_a = AggregationConfig()
    create_processing_worker(config_b, config_i, config_a)

if __name__ == "__main__":
    main()