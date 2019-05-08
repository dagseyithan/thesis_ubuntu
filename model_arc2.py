from keras.layers import Conv1D, Conv2D, BatchNormalization, MaxPooling2D, Dense, Reshape, Flatten, Input
from keras.models import Sequential, Model
from keras.utils import Sequence
import numpy as np
import pprint as pp
import tensorflow as tf
import text_utilities as tu
from data.datareader import read_original_products_data, read_dataset_data
from keras import backend as K
from elmo import __get_elmo_sentence_embedding, __get_elmo_word_embedding
from config.configurations import MAX_TEXT_WORD_LENGTH, ELMO_VECTOR_LENGTH, FASTTEXT_VECTOR_LENGTH

EMBEDDING_LENGTH = ELMO_VECTOR_LENGTH
COMBINATION_COUNT = 1944

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
    print(combined.shape)
    return np.reshape(combined, (combined.shape[0] * combined.shape[1], word_embedding_length)), combined.shape[0] * combined.shape[1]

class DataGenerator(Sequence):

    def __init__(self, x_set, y_set, batch_size):
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size)))

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        return np.array([resize(imread(file_name), (200, 200)) for file_name in batch_x]), np.array(batch_y)




input1 = np.zeros((MAX_TEXT_WORD_LENGTH, EMBEDDING_LENGTH), dtype=float)
input2 = np.zeros((MAX_TEXT_WORD_LENGTH, EMBEDDING_LENGTH), dtype=float)
input3 = np.zeros((MAX_TEXT_WORD_LENGTH, EMBEDDING_LENGTH), dtype=float)


text1 = "zwei wörter or mehr sind glaube ich besser"
text2 = "und drei wörter sind auch mehr als der erste"
text3 = "dies ist die zweite text"

text1_embedding = __get_elmo_sentence_embedding(text1)
#text1_embedding = [[1., 1., 1.], [12., 12., 12.], [13., 13., 13.],[14., 14., 14.], [15., 15., 15.], [16., 16., 16.]]
text1_word_length = len(text1.split())

text2_embedding = __get_elmo_sentence_embedding(text2)
#text2_embedding = [[2., 2., 2.], [22., 22., 22.], [23., 23., 23.], [24., 24., 24.], [25., 25., 25.], [26., 26., 26.]]
text2_word_length = len(text2.split())

text3_embedding = __get_elmo_sentence_embedding(text3)
#text3_embedding = [[2., 2., 2.], [22., 22., 22.], [23., 23., 23.], [24., 24., 24.], [25., 25., 25.], [26., 26., 26.]]
text3_word_length = len(text3.split())

input1[:text1_word_length] = text1_embedding[:MAX_TEXT_WORD_LENGTH]
input2[:text2_word_length] = text2_embedding[:MAX_TEXT_WORD_LENGTH]
input3[:text3_word_length] = text3_embedding[:MAX_TEXT_WORD_LENGTH]

#print(input1.size)
#combined = get_combinations(text1_embedding, text2_embedding, max_text_length = 6, embedding_length = 3, window_size = 3)
combined, combination_count = get_combinations(input1, input2, max_text_length = MAX_TEXT_WORD_LENGTH, word_embedding_length = EMBEDDING_LENGTH, window_size = 3)
#combined2 = get_combinations(input1, input3, max_text_length = MAX_TEXT_WORD_LENGTH, word_embedding_length = EMBEDDING_LENGTH, window_size = 3)

pp.pprint(combined)
print(combined.shape)



'''

Data = readdata()
ProductX, ProductY = Data[Data.columns[0]], Data[Data.columns[4]]

print(ProductX[0])
text, extracted, numerals = tu.pre_process(ProductX[0])
print(text)
embeddingsent = __get_elmo_sentence_embedding("zwei wörter")

'''
#combined = np.reshape(combined, (1, 1, combined.shape[0], combined.shape[1]))
#combined2 = np.reshape(combined2, (1, 1, combined2.shape[0], combined2.shape[1]))
#combined = np.append(combined, combined2, axis=0)
sent1 = combined
sent1 = np.expand_dims(sent1, axis=0)
print(sent1.shape)



def hinge_loss():
    return 0



def create_network(input_shape, combination_count):

    model = Sequential()
    model.add(BatchNormalization(input_shape = input_shape))
    model.add(Conv1D(filters=100, kernel_size=3, kernel_initializer='truncated_normal', input_shape=(None, EMBEDDING_LENGTH), use_bias=True, activation='relu', padding='same'))
    model.add(Reshape((COMBINATION_COUNT, 10, 10)))
    model.add(Conv2D(filters=20, kernel_size=(3, 3), kernel_initializer='truncated_normal', input_shape=(None, EMBEDDING_LENGTH), data_format='channels_first', use_bias=True, activation='relu', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format='channels_first'))
    model.add(Conv2D(filters=100, kernel_size=(3, 3), kernel_initializer='truncated_normal', input_shape=(None, EMBEDDING_LENGTH), data_format='channels_first', use_bias=True, activation='relu', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format=None))
    model.add(Conv2D(filters=100, kernel_size=(3, 3), kernel_initializer='truncated_normal', input_shape=(None, EMBEDDING_LENGTH), data_format='channels_first', use_bias=True, activation='relu', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format='channels_first'))
    model.add(Flatten())
    model.add(Dense(activation='relu', units=64, use_bias=True))
    model.add(Dense(activation='relu', units=32, use_bias=True))
    model.add(Dense(activation='softplus', units=1, use_bias=True))

    return model


pos_in = Input(shape=(combination_count, EMBEDDING_LENGTH))
neg_in = Input(shape=(combination_count, EMBEDDING_LENGTH))

net = create_network(input_shape=(None, EMBEDDING_LENGTH), combination_count = combination_count)

pos_out = net(pos_in)
neg_out = net(neg_in)
net_out = [pos_out, neg_out]

model = Model(inputs=[pos_in, neg_in], outputs=net_out)
model.compile(optimizer='adam', loss=hinge_loss)


model.fit(train_data, y_dummie, batch_size=256, epochs=10)


