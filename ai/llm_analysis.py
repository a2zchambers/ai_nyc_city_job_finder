# This code allows the rest of your application one common way to communicate with Llama


from langchain_community.llms import Ollama


llm = Ollama(
    model="llama3.2:1b",
    keep_alive="30m",
    num_predict=1500
)


def ask_llm(prompt):

    return llm.invoke(prompt)
