from rasa_nlu.model import Interpreter

# where model_directory points to the model folder
interpreter = Interpreter.load(r"D:\NLP\test")
print(interpreter.parse(u"hi"))
