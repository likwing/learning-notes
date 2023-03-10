import numpy as np
from gensim.models import Word2Vec
from configs.config import *
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.recurrent import LSTM
from keras.layers.embeddings import Embedding
from keras.callbacks import EarlyStopping, ModelCheckpoint


class LSTM_RNN_Model:
    def __init__(self, X, Y, X_test, Y_test, input_len=32, hidden_len=512, output_len=100, dropout=0.2, nb_epoch=100,
                 batch_size=256, model_architecture_file=model_architecture_file_path,
                 model_weights_file=model_weights_path, word_vector_file=poetry_gen_data_model_path,
                 vector_size=word_vector_dimension, model=None):
        self.X = X
        self.Y = Y
        self.X_test = X_test
        self.Y_test = Y_test
        self.input_len = input_len
        self.hidden_len = hidden_len
        self.output_len = output_len
        self.dropout = dropout
        self.nb_epoch = nb_epoch
        self.batch_size = batch_size
        self.model_architecture_file = model_architecture_file
        self.model_weights_file = model_weights_file
        self.word_vector_file = word_vector_file
        self.vector_size = vector_size
        if not model:
            self.model = Sequential()
        else:
            self.model = model

    def build(self):
        model = Word2Vec.load(self.word_vector_file)
        # adding 1 to account for 0th index (for masking)
        embedding_weights = np.zeros((self.output_len + 1, self.vector_size))
        for i in xrange(self.output_len + 1):
            embedding_weights[i, :] = model[model.index2word[i]]

        # use word2vec results to init the embedding weights
        self.model.add(Embedding(input_dim=self.output_len + 1, output_dim=self.vector_size,
                                 weights=[embedding_weights], mask_zero=True,
                                 input_length=self.input_len, trainable=False))
        self.model.add(LSTM(self.hidden_len, input_shape=(self.input_len, self.vector_size), return_sequences=True))
        self.model.add(Dropout(self.dropout))
        self.model.add(LSTM(self.hidden_len, return_sequences=False))
        self.model.add(Dropout(self.dropout))
        self.model.add(Dense(self.output_len))

        self.model.add(Activation('softmax'))

    def train(self):
        self.model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=["accuracy"])

        # add early stop to terminate current training epoch if the valuate loss doesn't reduce
        early_stop = EarlyStopping(verbose=1, patience=3, monitor='val_loss')
        model_check = ModelCheckpoint(self.model_architecture_file, monitor='val_loss', verbose=True,
                                      save_best_only=True)
        self.model.fit(self.X, self.Y, batch_size=self.batch_size, nb_epoch=self.nb_epoch,
                       validation_data=(self.X_test, self.Y_test), callbacks=[early_stop, model_check])
        # dump the model
        outf = open(self.model_architecture_file, 'w')
        outf.write(self.model.to_json())
        self.model.save_weights(self.model_weights_file, overwrite=True)
        outf.close()
