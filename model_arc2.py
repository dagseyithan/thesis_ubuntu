from keras.layers import Conv1D, Conv2D, BatchNormalization, MaxPooling2D, Dense, Reshape, Flatten, Input, concatenate, Lambda
from keras.models import Sequential, Model
import tensorflow as tf
import keras.backend as K
import numpy as np
from config.configurations import MAX_TEXT_WORD_LENGTH, ELMO_VECTOR_LENGTH, FASTTEXT_VECTOR_LENGTH
from data.generator import Native_DataGenerator_for_Arc2
from data.datareader import read_dataset_data
from texttovector import get_ready_vector


EMBEDDING_LENGTH = ELMO_VECTOR_LENGTH
COMBINATION_COUNT =  MAX_TEXT_WORD_LENGTH * 2 #1944
BATCH_SIZE = 5


def hinge_loss(y_true, y_pred, alpha = 0.4):

    slice_pos = lambda x: x[0:5,:]
    slice_neg = lambda x: x[5:10,:]

    positive = Lambda(slice_pos, output_shape=(BATCH_SIZE,1))(y_pred)
    negative = Lambda(slice_neg, output_shape=(BATCH_SIZE,1))(y_pred)

    #positive = K.reshape(positive, (BATCH_SIZE, ))
    #negative = K.reshape(negative, (BATCH_SIZE, ))

    basic_loss = tf.reduce_sum(positive, axis=0) - tf.reduce_sum(negative, axis=0) + alpha

    loss = tf.maximum(basic_loss, 0.0)

    return loss

def create_network(input_shape):

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


pos_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))
neg_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))


net = create_network(input_shape=(None, EMBEDDING_LENGTH))

pos_out = net(pos_in)
neg_out = net(neg_in)
net_out = concatenate([pos_out, neg_out], axis=0)


model = Model(inputs=[pos_in, neg_in], outputs=net_out)
model.compile(optimizer='adam', loss=hinge_loss)


data_generator = Native_DataGenerator_for_Arc2(batch_size=BATCH_SIZE)

model.fit_generator(generator=data_generator, shuffle=True, epochs=10, workers=20, use_multiprocessing=True)


