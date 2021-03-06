import tensorflow as tf
import tensorflow.contrib.slim as slim
from flowfairy.conf import settings
from util import lrelu, conv2d, maxpool2d, embedding, avgpool2d, GLU, causal_GLU
from functools import partial
import ops

from jbb.model1 import conv_net

learning_rate = settings.LEARNING_RATE
discrete_class = settings.DISCRETE_CLASS

class Net:

    def feedforward(self, x, y, frqid, frqid2, is_training=False):
        pred = conv_net(x, frqid, None, is_training)

        target_output = tf.reshape(y,[-1])
        prediction = tf.reshape(pred,[-1, discrete_class])

        # Define loss and optimizer
        cost = tf.losses.sparse_softmax_cross_entropy(logits = prediction,
                                                      labels = target_output,
                                                      scope='xentropy')

        correct_pred = tf.equal(tf.argmax(pred, 2), y)
        with tf.name_scope('accuracy'):
            accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

        #_, variance = tf.nn.moments(pred, axes=[2])
        #variance = tf.reduce_mean(variance)

        with tf.name_scope('uncertainty'):
            softmax = tf.nn.softmax(pred)
            uncertainty = 1 - tf.reduce_max(softmax, axis=2)
            overall_uncertainty = tf.reduce_mean(uncertainty)
            print(uncertainty)
            print(overall_uncertainty)


        return pred, cost, accuracy, uncertainty, overall_uncertainty

    def train(self, **kwargs):
        with tf.name_scope('train'):
            self.train_x = kwargs['x']
            self.train_y = kwargs['y']

            self.train_pred, self.train_cost, self.train_acc, self.train_uncertainty, self.train_ouncertainty = self.feedforward(is_training=True, **kwargs)
            self.optimizer = ops.train()

    def validation(self, **kwargs):
        with tf.name_scope('val'):
            self.val_x = kwargs['x']
            self.val_y = kwargs['y']

            self.val_pred, self.val_cost, self.val_acc, self.val_uncertainty, self.val_ouncertainty = self.feedforward(**kwargs)
            self.val_pred = tf.Print(self.val_pred, [kwargs['frqid'], kwargs['frqid2']], message='frqids: ')

    def begin(self, session):
        #session.run(self.init)
        pass

    def should_stop(self):
        return False
