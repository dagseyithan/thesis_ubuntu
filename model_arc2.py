from keras.layers import Conv1D, Conv2D, MaxPooling2D, Dense, Reshape, Flatten, Input, concatenate, Lambda
from keras.models import Sequential, Model, load_model
from keras.optimizers import Adam
import keras.backend as K
from config.configurations import MAX_TEXT_WORD_LENGTH, EMBEDDING_LENGTH, BATCH_SIZE
from data_utilities.generator import Native_DataGenerator_for_Arc2, get_combinations
from texttovector import get_ready_vector
import numpy as np


COMBINATION_COUNT = 1944 #MAX_TEXT_WORD_LENGTH * 2 #1944

TRAIN = True

def hinge_loss(y_true, y_pred, alpha = 1.0):

    anchor_pos_out = Lambda(lambda x: x[0:BATCH_SIZE,:], output_shape=(BATCH_SIZE,1))(y_pred)
    pos_anchor_out = Lambda(lambda x: x[BATCH_SIZE:BATCH_SIZE*2,:], output_shape=(BATCH_SIZE,1))(y_pred)
    anchor_neg_out = Lambda(lambda x: x[BATCH_SIZE*2:BATCH_SIZE*3,:], output_shape=(BATCH_SIZE,1))(y_pred)
    neg_anchor_out = Lambda(lambda x: x[BATCH_SIZE*3:BATCH_SIZE*4,:], output_shape=(BATCH_SIZE,1))(y_pred)
    pos_neg_out = Lambda(lambda x: x[BATCH_SIZE*4:BATCH_SIZE*5,:], output_shape=(BATCH_SIZE,1))(y_pred)
    neg_pos_out = Lambda(lambda x: x[BATCH_SIZE*5:BATCH_SIZE*6,:], output_shape=(BATCH_SIZE,1))(y_pred)


    basic_loss = alpha + (K.sum(anchor_neg_out, axis=-1) * K.sum(neg_anchor_out, axis=-1) * K.sum(pos_neg_out, axis=-1)
                          * K.sum(neg_pos_out, axis=-1)) - (K.sum(anchor_pos_out, axis=-1) * K.sum(pos_anchor_out, axis=-1))

    loss = K.mean(K.maximum(basic_loss, 0.0), axis=-1)

    return loss

def create_network(input_shape):

    model = Sequential()
    #model.add(BatchNormalization(input_shape = input_shape))
    model.add(Conv1D(filters=400, kernel_size=3, kernel_initializer='glorot_uniform', input_shape=(None, EMBEDDING_LENGTH), use_bias=True, activation='relu', padding='same'))
    model.add(Reshape((COMBINATION_COUNT, 20, 20)))
    model.add(Conv2D(filters=100, kernel_size=(3, 3), kernel_initializer='glorot_uniform', input_shape=(None, EMBEDDING_LENGTH), data_format='channels_first', use_bias=True, activation='relu', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format='channels_first'))
    model.add(Conv2D(filters=100, kernel_size=(3, 3), kernel_initializer='glorot_uniform', input_shape=(None, EMBEDDING_LENGTH), data_format='channels_first', use_bias=True, activation='relu', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format='channels_first'))
    #model.add(Conv2D(filters=100, kernel_size=(3, 3), kernel_initializer='truncated_normal', input_shape=(None, EMBEDDING_LENGTH), data_format='channels_first', use_bias=True, activation='relu', padding='same'))
    #model.add(MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format='channels_first'))
    model.add(Flatten())
    #model.add(BatchNormalization())
    model.add(Dense(activation='relu', units=128, use_bias=True))
    model.add(Dense(activation='relu', units=64, use_bias=True))
    model.add(Dense(activation='relu', units=32, use_bias=True))
    model.add(Dense(activation='relu', units=16, use_bias=True))
    model.add(Dense(activation='softplus', units=1, use_bias=True))

    return model

if TRAIN:
    anchor_pos_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))
    anchor_neg_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))
    neg_anchor_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))
    pos_anchor_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))
    pos_neg_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))
    neg_pos_in = Input(shape=(COMBINATION_COUNT, EMBEDDING_LENGTH))


    net = create_network(input_shape=(None, EMBEDDING_LENGTH))

    anchor_pos_out = net(anchor_pos_in)
    anchor_neg_out = net(anchor_neg_in)
    neg_anchor_out = net(neg_anchor_in)
    pos_anchor_out = net(pos_anchor_in)
    pos_neg_out = net(pos_neg_in)
    neg_pos_out = net(neg_pos_in)

    net_out = concatenate([anchor_pos_out, pos_anchor_out, anchor_neg_out, neg_anchor_out, pos_neg_out, neg_pos_out], axis=0)


    model = Model(inputs=[anchor_pos_in, anchor_neg_in, neg_anchor_in, pos_anchor_in, pos_neg_in, neg_pos_in], outputs=net_out)
    model.compile(optimizer=Adam(lr=0.0001), loss=hinge_loss)


    data_generator = Native_DataGenerator_for_Arc2(batch_size=BATCH_SIZE, mode='combination')

    #model = load_model('trained_models/model_arc2_02_concat.h5', custom_objects={'hinge_loss': hinge_loss})
    model.fit_generator(generator=data_generator, shuffle=True, epochs=10, workers=1, use_multiprocessing=False)
    model.save('trained_models/model_arc2_00_FastText_allpossiblecombinations.h5')
else:
    model = load_model('trained_models/model_arc2_01_mirroreddataset.h5', custom_objects={'hinge_loss': hinge_loss})
    model.summary()

def get_similarity_arc2(textA, textB):
    vector = np.reshape(get_combinations(get_ready_vector(textA), get_ready_vector(textB),
                                max_text_length=MAX_TEXT_WORD_LENGTH,
                                word_embedding_length=EMBEDDING_LENGTH), (1, COMBINATION_COUNT, EMBEDDING_LENGTH))
    return model.predict_on_batch([vector, vector])[0][0]

'''
print(get_similarity_arc2('Unterkonstruktion tepro Pent Roof 6x4 193 x 112 cm, silber', 'Unterk.Pent Roof 6x4für 7116/7209/7236'))
print(get_similarity_arc2('Unterkonstruktion tepro Pent Roof 6x4 193 x 112 cm, silber', 'Unterkonstruktion tepro Riverton 6x4 192,2 x 112,1 cm, silber'))
print(get_similarity_arc2('Unterkonstruktion tepro Pent Roof 6x4 193 x 112 cm, silber', 'Feuchtraumkabel NYM-J 3G1,5 10M'))
print(get_similarity_arc2('Unterkonstruktion tepro Pent Roof 6x4 193 x 112 cm, silber', 'Unterk.Riverton 6x4 HAUSTYP1/7124/7240'))
print(get_similarity_arc2('Unterkonstruktion tepro Riverton 6x4 192,2 x 112,1 cm, silber', 'Unterk.Pent Roof 6x4für 7116/7209/7236'))
print(get_similarity_arc2('Unterkonstruktion tepro Riverton 6x4 192,2 x 112,1 cm, silber', 'Unterk.Riverton 6x4 HAUSTYP1/7124/7240'))
print(get_similarity_arc2('Unterk.Riverton 6x4 HAUSTYP1/7124/7240', 'Unterkonstruktion tepro Pent Roof 6x4 193 x 112 cm, silber'))
print(get_similarity_arc2('Unterk.Riverton 6x4 HAUSTYP1/7124/7240', 'Unterkonstruktion tepro Riverton 6x4 192,2 x 112,1 cm, silber'))
'''


