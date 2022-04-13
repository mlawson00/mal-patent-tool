from fastapi import FastAPI
from official.nlp import bert
import official.nlp.bert.tokenization
import tensorflow_text
import requests
import json
from pydantic import BaseModel
toke = bert.tokenization.FullTokenizer('vocab.txt')
from fastapi.encoders import jsonable_encoder
app = FastAPI()
#
class custom_bert_encoder:
    def __init__(self, vocab_file, max_len=128):
        self.bert = bert.tokenization.FullTokenizer(vocab_file)
        self.max_len = max_len
    def bert_encode(self, text):
        text = self.bert.tokenize(text)
        text = text[: self.max_len - 2]
        input_sequence = ["[CLS]"] + text + ["[SEP]"]
        pad_len = self.max_len - len(input_sequence)
        tokens = self.bert.convert_tokens_to_ids(input_sequence) + [0] * pad_len
        pad_masks = [1] * len(input_sequence) + [0] * pad_len
        segment_ids = [0] * self.max_len
        return {"text":text, "input_mask":[pad_masks], "input_type_ids":[segment_ids], "input_word_ids":[tokens]}

b = custom_bert_encoder('vocab.txt')

class AbstractDraft(BaseModel):
    abstract: str

class BERT_input(BaseModel):
    input_mask: list
    input_type_ids: list
    input_word_ids: list


@app.get("/")
async def root():
    return {"message": "Hello World"}
#
@app.post("/abstract_search")
async def abstract_search(abstract_draft: AbstractDraft) -> AbstractDraft:
    raw_data = jsonable_encoder(abstract_draft.abstract)

    data = b.bert_encode(raw_data)
    #output = requests.post('http://localhost:8080/invocations', json={"inputs": data})
    return {"inputs": data}

@app.get("/get_cpc_probs/{input}")
async def make_cpc_pred(input):
    data = b.bert_encode(input)
    inputs = {"inputs": data}
    probs = requests.post('http://localhost:8080/invocations', json={"inputs": data})
    return {'probs':json.loads(probs.text)}


@app.post("/get_BERT_probs")
async def make_cpc_pred(bert_input: BERT_input)->BERT_input:
    probs = requests.post('http://localhost:8080/invocations', json={"inputs": bert_input.dict()})
    return {'probs':json.loads(probs.text)}