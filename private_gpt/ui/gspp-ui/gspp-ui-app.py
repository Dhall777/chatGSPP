# Flask, the UI app
from flask import Flask, render_template, request
# PGPT SDK, for easy API functionality
from pgpt_python.client import PrivateGPTApi

app = Flask(__name__)

# Initialize the PrivateGPT API client
api_client = PrivateGPTApi(base_url="http://localhost:8001")

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    source = None
    if request.method == 'POST':
        message = request.form['message']
        response, source = send_message_to_api(message)
    return render_template('index.html', response=response, source=source)

def send_message_to_api(message):
    try:
        result = api_client.contextual_completions.prompt_completion(
            prompt=message,
            use_context=True,
            context_filter={"docs_ids": ["147969f3-dd54-489b-88d1-bf3b07c83384"]},  # Adjust as needed
            include_sources=True,
            #timeout=300,
        ).choices[0]
        return result.message.content, result.sources[0].document.doc_metadata.get('file_name')
    except Exception as e:
        return str(e), None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
