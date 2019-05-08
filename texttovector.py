import numpy as np
import text_utilities as tu
from elmo import __get_elmo_sentence_embedding
from fasttext import __get_fasttext_sentence_embedding
from config.configurations import ELMO_VECTOR_LENGTH, MAX_TEXT_WORD_LENGTH, FASTTEXT_VECTOR_LENGTH



def get_ready_vector(text, padding = True, embedder = 'elmo'):
    text = tu.pre_process_single_return(text)
    text_word_length = len(text.split())
    if embedder == 'elmo': #CHANGE TO GLOBAL NEEDED
        EMBEDDING_LENGTH = ELMO_VECTOR_LENGTH
        embedding = __get_elmo_sentence_embedding(text)
    else:
        EMBEDDING_LENGTH = FASTTEXT_VECTOR_LENGTH
        embedding = __get_fasttext_sentence_embedding(text)
    if padding:
        padded = np.zeros((MAX_TEXT_WORD_LENGTH, EMBEDDING_LENGTH), dtype=float)
        padded[:text_word_length] = embedding[:MAX_TEXT_WORD_LENGTH]
        return padded
    else:
        return embedding