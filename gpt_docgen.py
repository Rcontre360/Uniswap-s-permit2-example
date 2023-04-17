import os
import requests

OUTPUT_FOLDER = 'documentation'
system_prompt = f"You are a documentation generator for solidity smart contracts. You are going to receive code in solidity and some context about the project. You are going to output documentation for the software you read, the target audience are going to be developers, so you need to explain each contract function clearly and taking in account the previous contracts you received. Each explanation must be concise and have correct hierarchy using markdonw, an example of this is creating a h2 header for a contract/interface and a h3 or h4 header for the functions, or bullet points for the arguments. Also, you're going to skip any information that you audience might already know, few examples are: the language in which the contracts are created (solidity), any information about the blockchain and how it works. Remember that your audience are solidity developers and they already know that, only focus on the purpose of each contract and how they work."
base_prompt = f"Generate documentation for the following Solidity smart contract in the markdown language:"

def get_code(file_path: str) -> list[str]:
    with open(file_path, 'r') as file:
        contract_code = file.read()

    tokens = contract_code.split()
    chunks = []

    while tokens:
        current_chunk = []
        current_length = 0

        while tokens and current_length + len(tokens[0]) <= 3000:
            token = tokens.pop(0)
            current_chunk.append(token)
            current_length += len(token)

        chunks.append(' '.join(current_chunk))

    if len(chunks) > 1:
        chunks[:-1] = [f"{chunk} Don't output documentation just yet, wait for the rest of the code, just answer with YES" for chunk in chunks[:-1]]
        chunks[-1] = f"{chunks[-1]} Now you can output documentation"
    else:
        chunks[0] = f"{chunks[0]} Now you can output documentation"

    return chunks

def generate_documentation(all_contracts_code: list[str]) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend([{"role": "user", "content": code} for code in all_contracts_code])

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": messages,
            'temperature': 0.3
        }
    )

    # if (len(all_contracts_code) > 1):
        # print(json.dumps(all_contracts_code))
        # print(json.dumps(response.json()['choices']))

    generated_text = response.json()['choices'][0]['message']['content']
    return generated_text

def process_directory(directory:str):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.sol'):
                file_path = os.path.join(root, file)
                contract_code = get_code(file_path)
                try:
                    documentation = generate_documentation(contract_code)
                except Exception as e:
                    documentation = ''
                create_markdown(documentation, file)

def create_markdown(documentation: str, contract_name: str, output_folder: str = OUTPUT_FOLDER):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Create the markdown file
    markdown_file = os.path.join(output_folder, f"{contract_name}_documentation.md")
    with open(markdown_file, "w") as f:
        f.write(documentation)
    print(f"Documentation for {contract_name} saved in {markdown_file}")

if __name__ == "__main__":
    contracts_directory = os.path.join(os.getcwd(), 'contracts')
    process_directory(contracts_directory)


