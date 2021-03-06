from keras.utils.data_utils import Sequence
import numpy as np
from data_utilities.datareader import read_dataset_data, read_original_products_data, read_sts_data, read_sick_data, read_msr_data
from texttovector import get_ready_vector, get_ready_vector_on_batch, get_ready_tensors, get_similarity_matrix
from config.configurations import MAX_TEXT_WORD_LENGTH, EMBEDDING_LENGTH
from encoder import encode_word, encode_number
from sklearn.preprocessing import minmax_scale
from structural import get_encoded_similarity
from keras.models import load_model
from config import configurations
import multiprocessing
import pandas as pd



COMBINATION_COUNT = 1944

DIM = 9
MAX_TEXT_WORD_LENGTH = configurations.MAX_TEXT_WORD_LENGTH
MAX_WORD_CHARACTER_LENGTH = configurations.MAX_WORD_CHARACTER_LENGTH
EMBEDDING_LENGTH = configurations.EMBEDDING_LENGTH
ALPHABET_LENGTH = configurations.ALPHABET_LENGTH
WORD_TO_WORD_COMBINATIONS = int(MAX_TEXT_WORD_LENGTH * MAX_TEXT_WORD_LENGTH)
WORD_TENSOR_DEPTH = int((ALPHABET_LENGTH * MAX_WORD_CHARACTER_LENGTH) / DIM)
BATCH_SIZE = configurations.BATCH_SIZE


def get_combinations_on_batch(batch_a, batch_b, max_text_length, word_embedding_length, window_size = 3):
    combined_as_batch = []
    assert batch_a.shape == batch_b.shape
    for vecA, vecB in zip(batch_a, batch_b):
        combined_as_batch.append(get_combinations(vecA, vecB, max_text_length, word_embedding_length, window_size))
    return np.array(combined_as_batch)




def get_combinations(vec_A, vec_B, max_text_length, word_embedding_length, window_size = 3):
    combined = []
    i, j = 0, 0
    while i+window_size <= max_text_length:
        while j+window_size <= max_text_length:
            stacked = np.vstack((vec_A[i:i+window_size], vec_B[j:j+window_size]))
            combined.append(list(stacked))
            j += 1
        j = 0
        i += 1
    combined = np.array(combined)
    return np.reshape(combined, (combined.shape[0] * combined.shape[1], word_embedding_length))


def get_concat(vec_A, vec_B, max_text_length, word_embedding_length, window_size = 3):
    return np.concatenate((vec_A, vec_B))


class Native_DataGenerator_for_StructuralSimilarityModel(Sequence):
    def __init__(self, batch_size):
        x_a = np.random.randint(0, 1001, (10000, 1))
        x_b = np.random.randint(0, 1001, (10000, 1))
        x_set = np.column_stack((x_a, x_b))
        y_set = minmax_scale(np.abs(x_a - x_b), feature_range=(0, 1))
        print(y_set)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        x_a = np.array([np.expand_dims(encode_number(number[0]), axis=0) for number in batch_x])
        x_b = np.array([np.expand_dims(encode_number(number[1]), axis=0) for number in batch_x])

        return [x_a, x_b], batch_y

class Native_DataGenerator_for_StructuralSimilarityModel_LSTMEncoder3x3(Sequence):
    def __init__(self, batch_size):
        x_set = []
        for i in range(1):
            for num in range(0, 262144):
                pad = np.zeros((18), dtype=float)
                arr = np.array([float(x) for x in bin(num)[2:]])
                pad[-len(arr):] = arr
                x_set.append(pad)

        x_set = np.array(x_set)
        print(x_set)
        x_set= np.reshape(x_set, (x_set.shape[0], x_set.shape[1], 1))
        np.random.shuffle(x_set)
        y_set = np.array([get_encoded_similarity(np.reshape(entry[0:9], (3, 3)), np.reshape(entry[9:18], (3,3))) for entry in x_set])
        print(y_set)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        return batch_x, batch_y


class Native_DataGenerator_for_StructuralSimilarityModel_SimilaritySpace3x3(Sequence):
    def __init__(self, batch_size):
        encoder3x3 = load_model(
            'C:\\Users\\seyit\\PycharmProjects\\thesis\\trained_models\\model_structuralsimilarity_autoencoder3x3_4dim_embeddings_encoder.h5')
        print('encoder3x3 model has been loaded...')
        x_set = []
        x_set_strings = []
        for i in range(1):
            for num in range(0, 512):
                pad = np.zeros((9), dtype=float)
                arr = np.array([float(x) for x in bin(num)[2:]])
                pad[-len(arr):] = arr
                x_set_binary = []
                encoded_vectors = []
                x_set_binary.append(pad)
                encoded_vectors.append(encoder3x3.predict(np.array([pad]))[0])
                for num2 in range(0, 512):
                    pad = np.zeros((9), dtype=float)
                    arr = np.array([float(x) for x in bin(num2)[2:]])
                    pad[-len(arr):] = arr
                    x_set_binary.append(pad)
                    encoded_vectors.append(encoder3x3.predict(np.array([pad]))[0])
                    x_set.append(np.array(encoded_vectors))
                    x_set_strings.append(x_set_binary)
                    encoded_vectors = [encoded_vectors[0]]
                    x_set_binary = [x_set_binary[0]]

        x_set = np.array(x_set)
        x_set_strings = np.array(x_set_strings)
        y_set = np.array([get_encoded_similarity(np.reshape(entry[0], (3, 3)), np.reshape(entry[1], (3, 3))) for entry in x_set_strings])
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        vec_a = np.array([vec[0] for vec in batch_x])
        vec_b = np.array([vec[1] for vec in batch_x])

        return [vec_a, vec_b], batch_y

class Native_DataGenerator_for_StructuralSimilarityModel_Autoencoder(Sequence):
    def __init__(self, batch_size):
        x_set = []
        for i in range(20):
            for num in range(0, 16):
                pad = np.zeros((4), dtype=float)
                arr = np.array([float(x) for x in bin(num)[2:]])
                pad[-len(arr):] = arr
                x_set.append(pad)

        x_set = np.array(x_set)#np.random.randint(2, size = (10000, 9)).astype(np.float)#read_german_words_dictionary()
        np.random.shuffle(x_set)
        y_set = x_set
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        return batch_x, batch_y


class Native_DataGenerator_for_IndependentModel(Sequence):
    def __init__(self, batch_size):
        data = read_dataset_data('train')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), \
                           data[data.columns[2]].to_numpy()
        #mirrored_ap = np.append(np.append(anchor, pos), np.append(anchor, pos))
        #mirrored_pa = np.append(np.append(pos, anchor), np.append(anchor, pos))
        #mirrored_nn = np.append(np.append(neg, neg), np.append(neg, neg))
        #x_set = np.column_stack((mirrored_ap, mirrored_pa, mirrored_nn))
        x_set = np.column_stack((anchor, pos, neg))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]


        anchor_in = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        pos_in = np.array([get_ready_vector(sample[1]) for sample in batch_x])
        neg_in = np.array([get_ready_vector(sample[2]) for sample in batch_x])


        return [anchor_in, pos_in, neg_in], batch_y


class Native_DataGenerator_for_Arc2(Sequence):

    def __init__(self, batch_size, mode = 'combination'):
        data = read_dataset_data('train')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), data[data.columns[2]].to_numpy()
        #mirrored_ap = np.append(anchor, pos)
        #mirrored_pa = np.append(pos, anchor)
        #mirrored_nn = np.append(neg, neg)
        #x_set = np.column_stack((mirrored_ap, mirrored_pa, mirrored_nn))
        x_set = np.column_stack((anchor, pos, neg))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size
        self.mode = mode

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        if self.mode == 'combination':

            anchor_pos = np.array([get_combinations(get_ready_vector(sample[0]), get_ready_vector(sample[1]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
            pos_anchor = np.array([get_combinations(get_ready_vector(sample[1]), get_ready_vector(sample[0]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
            anchor_neg = np.array([get_combinations(get_ready_vector(sample[0]), get_ready_vector(sample[2]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
            neg_anchor = np.array([get_combinations(get_ready_vector(sample[2]), get_ready_vector(sample[0]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
            pos_neg = np.array([get_combinations(get_ready_vector(sample[1]), get_ready_vector(sample[2]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
            neg_pos = np.array([get_combinations(get_ready_vector(sample[2]), get_ready_vector(sample[1]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])

        else: #TODO
            anchor_pos = np.array([get_concat(get_ready_vector(sample[0]), get_ready_vector(sample[1]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])

            anchor_neg = np.array([get_concat(get_ready_vector(sample[0]), get_ready_vector(sample[2]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
                                                

        return [anchor_pos, pos_anchor, anchor_neg, neg_anchor, pos_neg, neg_pos], batch_y


class Native_DataGenerator_for_Arc2_on_batch(Sequence):

    def __init__(self, batch_size, mode='combination'):
        data = read_dataset_data('train')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), \
                           data[data.columns[2]].to_numpy()
        mirrored_ap = np.append(anchor, pos)
        mirrored_pa = np.append(pos, anchor)
        mirrored_nn = np.append(neg, neg)
        x_set = np.column_stack((mirrored_ap, mirrored_pa, mirrored_nn))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size
        self.mode = mode

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        if self.mode == 'combination':
            batch_anchor = [sample[0] for sample in batch_x]
            batch_pos = [sample[1] for sample in batch_x]
            batch_neg = [sample[2] for sample in batch_x]

            anchor_pos = get_combinations_on_batch(get_ready_vector_on_batch(batch_anchor),
                                                   get_ready_vector_on_batch(batch_pos),
                                                   max_text_length=MAX_TEXT_WORD_LENGTH,
                                                   word_embedding_length=EMBEDDING_LENGTH)
            anchor_neg = get_combinations_on_batch(get_ready_vector_on_batch(batch_anchor),
                                                   get_ready_vector_on_batch(batch_neg),
                                                   max_text_length=MAX_TEXT_WORD_LENGTH,
                                                   word_embedding_length=EMBEDDING_LENGTH)
        '''
        #TODO
        else:
            anchor_pos = np.array([get_concat(get_ready_vector(sample[0]), get_ready_vector(sample[1]),
                                              max_text_length=MAX_TEXT_WORD_LENGTH,
                                              word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])

            anchor_neg = np.array([get_concat(get_ready_vector(sample[0]), get_ready_vector(sample[2]),
                                              max_text_length=MAX_TEXT_WORD_LENGTH,
                                              word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
        '''
        return [anchor_pos, anchor_neg], batch_y


class Native_Test_DataGenerator_for_Arc2(Sequence):

    def __init__(self, textA):
        Data = read_original_products_data()
        textB = Data[Data.columns[4]].to_numpy() #all ProductY
        self.textA = textA
        self.x = textB

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        test_vector = np.reshape(np.array(get_combinations(get_ready_vector(self.textA), get_ready_vector(self.x[idx]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH)), (1, COMBINATION_COUNT, EMBEDDING_LENGTH))

        return [test_vector, test_vector]


def DataGenerator_for_Arc2(batch_size):
    data = read_dataset_data('train')
    anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), data[data.columns[2]].to_numpy()
    x = np.column_stack((anchor, pos, neg))
    y = np.zeros((x.shape[0]), dtype=float)
    DATASET_SIZE = x.shape[0]

    while True:
        for i in range(0, DATASET_SIZE):
            batch_x = x[i * batch_size:(i + 1) * batch_size]
            batch_y = y[i * batch_size:(i + 1) * batch_size]

            anchor_pos = np.array([get_combinations(get_ready_vector(sample[0]), get_ready_vector(sample[1]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])
            anchor_neg = np.array([get_combinations(get_ready_vector(sample[0]), get_ready_vector(sample[2]),
                                                    max_text_length=MAX_TEXT_WORD_LENGTH,
                                                    word_embedding_length=EMBEDDING_LENGTH) for sample in batch_x])

            yield [anchor_pos, anchor_neg], np.array(batch_y)



class Native_DataGenerator_for_SemanticSimilarityNetwork_STS(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, scores = read_sts_data('train')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = scores
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        '''
        input_k = np.array([print(sample[0]) for sample in batch_x])
        input_c = np.array([print(sample[1]) for sample in batch_x])
        input_m = np.array([print(sample) for sample in batch_y])

        input('\n')
        '''
        input_A = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        input_B = np.array([get_ready_vector(sample[1]) for sample in batch_x])

        return [input_A, input_B], batch_y

class Native_ValidationDataGenerator_for_SemanticSimilarityNetwork_STS(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, scores = read_sts_data('test')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = scores
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        '''
        input_k = np.array([print(sample[0]) for sample in batch_x])
        input_c = np.array([print(sample[1]) for sample in batch_x])
        input_m = np.array([print(sample) for sample in batch_y])

        input('\n')
        '''
        input_A = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        input_B = np.array([get_ready_vector(sample[1]) for sample in batch_x])

        return [input_A, input_B], batch_y


class Native_DataGenerator_for_SemanticSimilarityNetwork_SICK(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_sick_data('train')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        '''
        input_k = np.array([print(sample[0]) for sample in batch_x])
        input_c = np.array([print(sample[1]) for sample in batch_x])
        input_m = np.array([print(sample) for sample in batch_y])

        input('\n')
        '''
        input_A = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        input_B = np.array([get_ready_vector(sample[1]) for sample in batch_x])

        return [input_A, input_B], batch_y

class Native_ValidationDataGenerator_for_SemanticSimilarityNetwork_SICK(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_sick_data('test')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        '''
        input_k = np.array([print(sample[0]) for sample in batch_x])
        input_c = np.array([print(sample[1]) for sample in batch_x])
        input_m = np.array([print(sample) for sample in batch_y])

        input('\n')
        '''
        input_A = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        input_B = np.array([get_ready_vector(sample[1]) for sample in batch_x])

        return [input_A, input_B], batch_y


class Native_DataGenerator_for_SemanticSimilarityNetwork_MSR(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_msr_data('train')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        '''
        input_k = np.array([print(sample[0]) for sample in batch_x])
        input_c = np.array([print(sample[1]) for sample in batch_x])
        input_m = np.array([print(sample) for sample in batch_y])

        input('\n')
        '''
        input_A = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        input_B = np.array([get_ready_vector(sample[1]) for sample in batch_x])

        return [input_A, input_B], batch_y

class Native_ValidationDataGenerator_for_SemanticSimilarityNetwork_MSR(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_msr_data('test')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        '''
        input_k = np.array([print(sample[0]) for sample in batch_x])
        input_c = np.array([print(sample[1]) for sample in batch_x])
        input_m = np.array([print(sample) for sample in batch_y])

        input('\n')
        '''
        input_A = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        input_B = np.array([get_ready_vector(sample[1]) for sample in batch_x])

        return [input_A, input_B], batch_y


class Native_DataGenerator_for_UnificationNetwork_SICK(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_sick_data('train')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        prepared_batch = np.array(list(map(prepare_batch, batch_x)))

        return [np.stack(prepared_batch[:, 0], axis=0),
                np.stack(prepared_batch[:, 1], axis=0),
                np.stack(prepared_batch[:, 2], axis=0),
                np.stack(prepared_batch[:, 3], axis=0),
                np.stack(prepared_batch[:, 4], axis=0),
                np.stack(prepared_batch[:, 5], axis=0),
                np.stack(prepared_batch[:, 6], axis=0),
                np.stack(prepared_batch[:, 7], axis=0)], batch_y


class Native_ValidationDataGenerator_for_UnificationNetwork_SICK(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_sick_data('test')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size


    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        prepared_batch = np.array(list(map(prepare_batch, batch_x)))

        return [np.stack(prepared_batch[:, 0], axis=0),
                np.stack(prepared_batch[:, 1], axis=0),
                np.stack(prepared_batch[:, 2], axis=0),
                np.stack(prepared_batch[:, 3], axis=0),
                np.stack(prepared_batch[:, 4], axis=0),
                np.stack(prepared_batch[:, 5], axis=0),
                np.stack(prepared_batch[:, 6], axis=0),
                np.stack(prepared_batch[:, 7], axis=0)], batch_y

class Native_DataGenerator_for_UnificationNetwork_MSR(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_msr_data('train')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        prepared_batch = np.array(list(map(prepare_batch, batch_x)))

        return [np.stack(prepared_batch[:, 0], axis=0),
                np.stack(prepared_batch[:, 1], axis=0),
                np.stack(prepared_batch[:, 2], axis=0),
                np.stack(prepared_batch[:, 3], axis=0),
                np.stack(prepared_batch[:, 4], axis=0),
                np.stack(prepared_batch[:, 5], axis=0),
                np.stack(prepared_batch[:, 6], axis=0),
                np.stack(prepared_batch[:, 7], axis=0)], batch_y


class Native_ValidationDataGenerator_for_UnificationNetwork_MSR(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_msr_data('test')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size


    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        prepared_batch = np.array(list(map(prepare_batch, batch_x)))

        return [np.stack(prepared_batch[:, 0], axis=0),
                np.stack(prepared_batch[:, 1], axis=0),
                np.stack(prepared_batch[:, 2], axis=0),
                np.stack(prepared_batch[:, 3], axis=0),
                np.stack(prepared_batch[:, 4], axis=0),
                np.stack(prepared_batch[:, 5], axis=0),
                np.stack(prepared_batch[:, 6], axis=0),
                np.stack(prepared_batch[:, 7], axis=0)], batch_y


class Native_DataGenerator_for_UnificationNetwork_STS(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_sts_data('train')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        prepared_batch = np.array(list(map(prepare_batch, batch_x)))

        return [np.stack(prepared_batch[:, 0], axis=0),
                np.stack(prepared_batch[:, 1], axis=0),
                np.stack(prepared_batch[:, 2], axis=0),
                np.stack(prepared_batch[:, 3], axis=0),
                np.stack(prepared_batch[:, 4], axis=0),
                np.stack(prepared_batch[:, 5], axis=0),
                np.stack(prepared_batch[:, 6], axis=0),
                np.stack(prepared_batch[:, 7], axis=0)], batch_y


class Native_ValidationDataGenerator_for_UnificationNetwork_STS(Sequence):
    def __init__(self, batch_size):
        sentences_A, sentences_B, labels = read_sts_data('test')
        x_set = np.column_stack((sentences_A, sentences_B))
        y_set = labels
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size


    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        prepared_batch = np.array(list(map(prepare_batch, batch_x)))

        return [np.stack(prepared_batch[:, 0], axis=0),
                np.stack(prepared_batch[:, 1], axis=0),
                np.stack(prepared_batch[:, 2], axis=0),
                np.stack(prepared_batch[:, 3], axis=0),
                np.stack(prepared_batch[:, 4], axis=0),
                np.stack(prepared_batch[:, 5], axis=0),
                np.stack(prepared_batch[:, 6], axis=0),
                np.stack(prepared_batch[:, 7], axis=0)], batch_y


class Native_DataGenerator_for_SemanticSimilarityNetwork_TM(Sequence):
    def __init__(self, batch_size):
        data = read_dataset_data('train')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), \
                           data[data.columns[2]].to_numpy()
        #mirrored_ap = np.append(np.append(anchor, pos), np.append(anchor, pos))
        #mirrored_pa = np.append(np.append(pos, anchor), np.append(anchor, pos))
        #mirrored_nn = np.append(np.append(neg, neg), np.append(neg, neg))
        #x_set = np.column_stack((mirrored_ap, mirrored_pa, mirrored_nn))
        x_set = np.column_stack((anchor, pos, neg))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]


        anchor_in = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        pos_in = np.array([get_ready_vector(sample[1]) for sample in batch_x])
        neg_in = np.array([get_ready_vector(sample[2]) for sample in batch_x])


        return [anchor_in, pos_in, neg_in], batch_y

class Native_ValidationDataGenerator_for_SemanticSimilarityNetwork_TM(Sequence):
    def __init__(self, batch_size):
        data = read_dataset_data('test')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), \
                           data[data.columns[2]].to_numpy()
        #mirrored_ap = np.append(np.append(anchor, pos), np.append(anchor, pos))
        #mirrored_pa = np.append(np.append(pos, anchor), np.append(anchor, pos))
        #mirrored_nn = np.append(np.append(neg, neg), np.append(neg, neg))
        #x_set = np.column_stack((mirrored_ap, mirrored_pa, mirrored_nn))
        x_set = np.column_stack((anchor, pos, neg))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]


        anchor_in = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        pos_in = np.array([get_ready_vector(sample[1]) for sample in batch_x])
        neg_in = np.array([get_ready_vector(sample[2]) for sample in batch_x])


        return [anchor_in, pos_in, neg_in], batch_y

class Native_DataGenerator_for_UnificationNetwork_TM(Sequence):
    def __init__(self, batch_size):
        data = read_dataset_data('train')
        anch_pos_sim = np.load('./anch_pos_sim_train.npy')
        anch_neg_sim = np.load('./anch_neg_sim_train.npy')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), \
                           data[data.columns[2]].to_numpy()

        x_set = np.column_stack((anchor, pos, neg))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y, self.x_set_sim_ap, self.x_set_sim_an = x_set, y_set, anch_pos_sim, anch_neg_sim
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_x_sim_ap= self.x_set_sim_ap[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_x_sim_an = self.x_set_sim_an[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        anchor_in = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        pos_in = np.array([get_ready_vector(sample[1]) for sample in batch_x])
        neg_in = np.array([get_ready_vector(sample[2]) for sample in batch_x])

        return [anchor_in, pos_in, neg_in, batch_x_sim_ap, batch_x_sim_an], batch_y

class Native_ValidationDataGenerator_for_UnificationNetwork_TM(Sequence):
    def __init__(self, batch_size):
        data = read_dataset_data('test')
        anch_pos_sim = np.load('./anch_pos_sim_test.npy')
        anch_neg_sim = np.load('./anch_neg_sim_test.npy')
        anchor, pos, neg = data[data.columns[0]].to_numpy(), data[data.columns[1]].to_numpy(), \
                           data[data.columns[2]].to_numpy()
        x_set = np.column_stack((anchor, pos, neg))
        y_set = np.zeros((x_set.shape[0]), dtype=float)
        self.x, self.y, self.x_set_sim_ap, self.x_set_sim_an = x_set, y_set, anch_pos_sim, anch_neg_sim
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size))) - 1

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_x_sim_ap = self.x_set_sim_ap[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_x_sim_an = self.x_set_sim_an[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        anchor_in = np.array([get_ready_vector(sample[0]) for sample in batch_x])
        pos_in = np.array([get_ready_vector(sample[1]) for sample in batch_x])
        neg_in = np.array([get_ready_vector(sample[2]) for sample in batch_x])

        return [anchor_in, pos_in, neg_in, batch_x_sim_ap, batch_x_sim_an], batch_y

def prepare_batch(sample):
    embedded_sentence_A = get_ready_vector(sample[0])
    embedded_sentence_B = get_ready_vector(sample[1])

    a, a_r, am, am_r = get_ready_tensors(sample[0])
    b, b_r, bm, bm_r = get_ready_tensors(sample[1])
    mask = np.logical_or(am, bm) * 1
    mask_r = np.logical_or(am_r, bm_r) * 1

    a = np.repeat(a, [MAX_TEXT_WORD_LENGTH], axis=0)
    a = np.reshape(a, (WORD_TO_WORD_COMBINATIONS * WORD_TENSOR_DEPTH, 9))
    a_r = np.repeat(a_r, [MAX_TEXT_WORD_LENGTH], axis=0)
    a_r = np.reshape(a_r, (WORD_TO_WORD_COMBINATIONS * WORD_TENSOR_DEPTH, 9))
    b = np.expand_dims(b, axis=0)
    b = np.repeat(b, [MAX_TEXT_WORD_LENGTH], axis=0)
    b = np.reshape(b, (WORD_TO_WORD_COMBINATIONS * WORD_TENSOR_DEPTH, 9))
    b_r = np.expand_dims(b_r, axis=0)
    b_r = np.repeat(b_r, [MAX_TEXT_WORD_LENGTH], axis=0)
    b_r = np.reshape(b_r, (WORD_TO_WORD_COMBINATIONS * WORD_TENSOR_DEPTH, 9))
    mask = np.repeat(mask, [MAX_TEXT_WORD_LENGTH], axis=0)
    mask_r = np.repeat(mask_r, [MAX_TEXT_WORD_LENGTH], axis=0)

    return embedded_sentence_A, embedded_sentence_B, a, b, a_r, b_r, mask, mask_r