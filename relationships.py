import os
from flask import Flask, request, render_template_string
from openai import OpenAI
from plantweb.render import render_file

client = OpenAI()

app = Flask(__name__)

# Define route for home page
@app.route("/", methods=["GET", "POST"])
def home():
    response_content = None
    rendered_graph = None
    if request.method == "POST":
        specification = request.form.get("specification")
        # Generate relationships using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who answers all questions extremely concisely."},
                {"role": "user", "content": f"Please identify all the major entities and relationships in the following design specification: {specification}"},
            ]
        )
        response_content = response.choices[0].message.content
        uml_generated = False
        # Generate PlantUML code using OpenAI
        while(not uml_generated):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant who generates PlantUML codes. Don't write anything except for the codes. Don't include anything before the @startuml or after the @enduml(Do not write the word plantuml before)"},
                        {"role": "user", "content": f"Please generate PlantUML codes for the following specification: {specification}"},
                    ]
                )
                plantUML_codes = response.choices[0].message.content.strip()
                infile = 'plantuml.dot'
                with open(infile, 'wb') as fd:
                    fd.write(plantUML_codes.encode('utf-8'))

                # Render the PlantUML diagram
                static_folder = os.path.join(os.getcwd(), "static")
                os.makedirs(static_folder, exist_ok=True)  # Ensure the static folder exists
                
                outfile = render_file(
                    infile,
                    renderopts={'format': 'png'},
                    cacheopts={'use_cache': False}
                )

                # Move the file to the static folder
                output_path = os.path.join(static_folder, "plantuml.png")
                os.replace(outfile, output_path)
                uml_generated = True

            except Exception as e:
                print("Failed to generate code, retrying")

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relationship Identifier</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #fff;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            h1 {
                text-align: center;
                color: #2c3e50;
            }
            label {
                display: block;
                margin-bottom: 10px;
                font-weight: bold;
            }
            textarea {
                width: 100%;
                padding: 10px;
                margin-bottom: 20px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 16px;
            }
            button {
                display: inline-block;
                background-color: #3498db;
                color: #fff;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
            }
            button:hover {
                background-color: #2980b9;
            }
            .response {
                margin-top: 20px;
                padding: 15px;
                background-color: #e8f8f5;
                border: 1px solid #b2dfdb;
                border-radius: 4px;
                font-family: "Courier New", Courier, monospace;
                white-space: pre-wrap;
            }
            .diagram {
                text-align: center;
                margin-top: 20px;
            }
            .diagram img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Relationship Identifier</h1>
            <form method="post">
                <label for="specification">Enter Design Specification:</label>
                <textarea id="specification" name="specification" rows="5" placeholder="Enter your design specification here..."></textarea>
                <button type="submit">Submit</button>
            </form>
            {% if response_content %}
                <div class="response">
                    <h2>Generated Response:</h2>
                    <p>{{ response_content }}</p>
                </div>
            {% endif %}
            {% if response_content %}
                <div class="response">
                    <img src="static/plantuml.png" alt="Generated Diagram">
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, response_content=response_content)

if __name__ == "__main__":
    app.run(debug=True)
