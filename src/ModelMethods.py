# import HappyTextToText from Happy Transformer
from happytransformer import HappyTextToText, TTSettings

# Huggingface Transformers
from transformers import (
    MT5ForConditionalGeneration,
    MT5Tokenizer,
    MBartForConditionalGeneration,
    MBartTokenizer,
    T5ForConditionalGeneration,
    T5TokenizerFast,
    GenerationConfig,
)

import torch
import re


"""
    Some global variables
    Add path to the models here
"""
mt5ModelPath = "../models/nep-spell-hft-23epochs"
mbartModelPath = "../models/happytt_mBART_plus_10"
vartat5ModelPath = "../models/vartat5-using-100K-plus-1"


"""
    Function: generate

    This function takes a model name and input text as parameters and 
    returns the output text generated by the specified model. 
    It supports multiple models such as mT5, mBART, and VartaT5. 
    If the specified model is not available, 
    it returns a message indicating the unavailability of the model.

    Parameters:
    - model (str): Name of the model to use for text generation.
    - input (str): Input text for the model to generate output from.

    Returns:
    - str: Output text generated by the specified model or a message indicating model unavailability.
"""


def generate(model, input):

    if model == "mT5":
        return mt5Inference(input)
    elif model == "mBART":
        return mbartInference(input)
    elif model == "VartaT5":
        return vartat5Inference(input)
    else:
        return f"Model: {model} not available"

    # काकाले काकिलाइ माया गर्नू हुन्छ।



"""
    Below are the 3 different models for inference
"""
def mt5Inference(input):
    print("Processing mt5")

    model = MT5ForConditionalGeneration.from_pretrained(mt5ModelPath)
    tokenizer = MT5Tokenizer.from_pretrained(mt5ModelPath)
    input_ids = tokenizer("grammar: " + input, return_tensors="pt").input_ids
    outputs = model.generate(
        input_ids=input_ids,
        max_length=512,
        num_beams=5,
        num_return_sequences=5,
        return_dict_in_generate=True,
        output_scores=True,
    )
    sequences = tokenizer.batch_decode(outputs.sequences, skip_special_tokens=True)
    return postProcessOutput(sequences,outputs["sequences_scores"])


def mbartInference(input):
    print("Processing mbart")
    tokenizer = MBartTokenizer.from_pretrained(
        mbartModelPath, src_lang="ne_NP", tgt_lang="ne_NP"
    )
    model = MBartForConditionalGeneration.from_pretrained(mbartModelPath)
    inputs = tokenizer("grammar: " + input, return_tensors="pt")
    outputs = model.generate(
        **inputs,
        decoder_start_token_id=tokenizer.lang_code_to_id["ne_NP"],
        max_length=512,
        num_beams=5,
        num_return_sequences=5,
        return_dict_in_generate=True,
        output_scores=True,
    )
    sequences = tokenizer.batch_decode(outputs.sequences, skip_special_tokens=True)
    return postProcessOutput(sequences, outputs["sequences_scores"])
    # return outputs


def vartat5Inference(input):
    print("Processing varta")
    model = T5ForConditionalGeneration.from_pretrained(vartat5ModelPath)
    # return "model ready"
    tokenizer = T5TokenizerFast.from_pretrained(vartat5ModelPath)
    input_ids = tokenizer("grammar: " + input, return_tensors="pt")
    outputs = model.generate(
        **input_ids,
        max_length=512,
        num_beams=5,
        num_return_sequences=5,
        return_dict_in_generate=True,
        output_scores=True,
    )
    sequences = tokenizer.batch_decode(outputs["sequences"], skip_special_tokens=True)
    return postProcessOutput(sequences,outputs["sequences_scores"])



"""
    Post processing the model output
"""

def postProcessOutput(sequences, sequences_scores):
    probabilities = torch.exp(sequences_scores)
    unique_sequences = set()
    # Initialize the list to store filtered items
    filtered_outputs = []

    # Iterate through sequences and formatted_scores
    for sequence, score in zip(sequences, probabilities):
        # Check if the sequence is not in the set of unique sequences
        if sequence not in unique_sequences:
            # Add the sequence to the set of unique sequences
            unique_sequences.add(sequence)
            # Append the sequence and score to the filtered_outputs list
            filtered_outputs.append({"sequence": sequence, "score": score.item()})

    return filtered_outputs


"""
    For working with paragraph processing
"""

def split_nepali_paragraph_into_sentences(nepali_text):

    # Define a regex pattern to split sentences
    # We'll split on periods, question marks, and exclamation marks
    sentence_pattern = r"(?<=[।?!\n])\s+"

    # Split the Nepali text into sentences
    sentences = re.split(sentence_pattern, nepali_text)

    return sentences


def process_paragraph(model, paragraph):
    sentenceList = split_nepali_paragraph_into_sentences(paragraph)
    out_sentence = []
    for s in sentenceList:
        out_sentence.append(generate(model, s))
    nepali_paragraph = " ".join(out_sentence)
    return nepali_paragraph
