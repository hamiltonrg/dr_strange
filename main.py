from shiny import App, ui, render, reactive
import ollama
import json
from ollama import ShowResponse
from datetime import datetime

# --- Helper Functions ---

def get_available_models():
    """Retrieves the list of available models from the Ollama server."""
    try:
        return [model['model'] for model in ollama.list().get('models', [])]
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return ["Error: Could not connect to Ollama. Is it running?"]

def datetime_converter(o):
    """Converts datetime objects to ISO 8601 strings for JSON serialization."""
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def get_model_config(model_name: str) -> tuple[dict | None, str | None]:
    """Fetches the configuration details for a specific model from Ollama."""
    try:
        config: ShowResponse = ollama.show(model_name)
        config_dict = config.model_dump()
        system_prompt = config_dict.get("system")
        return config_dict, system_prompt
    except Exception as e:
        print(f"Error getting config for {model_name}: {e}")
        return None, None

def format_model_config(config_dict: dict) -> str:
    """Formats the model configuration dictionary into a JSON string for display."""
    return json.dumps(config_dict, indent=2, default=datetime_converter)

# --- UI ---

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            "selected_model",
            "Select a Model:",
            choices=get_available_models(),
        ),
        ui.input_action_button("submit_model", "Submit Model"),
    ),
    ui.output_text_verbatim("submitted_model_output"),
    ui.output_text_verbatim("system_prompt_output"),
    ui.output_text_verbatim("model_config_output"),
)

# --- Server ---

def server(input, output, session):
    """Defines the server-side logic for the Shiny application."""
    model_to_display = reactive.Value("No model submitted yet.")
    model_config = reactive.Value("Model config will be shown here after submission.")
    system_prompt = reactive.Value("No system prompt configured")

    @reactive.Effect
    @reactive.event(input.submit_model)
    def _():
        """Handles the event when the 'Submit Model' button is clicked."""
        selected_model = input.selected_model()

        if "Error" in selected_model:
            ui.notification_show("Ollama is not running or is not accessible", type="error")
            model_to_display.set("Error: Could not connect to Ollama.")
            model_config.set("Error: Could not connect to Ollama.")
            system_prompt.set("Error: Could not connect to Ollama.")
            return

        model_to_display.set(f"You submitted model: {selected_model}")
        config_dict, extracted_system_prompt = get_model_config(selected_model)

        if config_dict is None:
            model_config.set(f"Error getting config for {selected_model}")
            system_prompt.set(f"Error getting config for {selected_model}")
            ui.notification_show(f"Error getting config for {selected_model}", type="error")
            return

        model_config.set(format_model_config(config_dict))

        if extracted_system_prompt:
            system_prompt.set(extracted_system_prompt)
        else:
            system_prompt.set("No system prompt configured")

    @output
    @render.text
    def submitted_model_output():
        """Renders the text output for the submitted model name."""
        return model_to_display.get()

    @output
    @render.text
    def system_prompt_output():
        """Renders the text output for the model's system prompt."""
        return system_prompt.get()

    @output
    @render.text
    def model_config_output():
        """Renders the text output for the model's configuration details."""
        return model_config.get()

app = App(app_ui, server)
