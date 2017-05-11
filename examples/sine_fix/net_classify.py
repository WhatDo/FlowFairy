import tensorflow as tf
import tensorflow.contrib.slim as slim
from flowfairy.conf import settings
from util import lrelu, conv2d, maxpool2d, embedding, avgpool2d, GLU, causal_GLU

discrete_class = settings.DISCRETE_CLASS
batch_size = settings.BATCH_SIZE
samplerate = sr = settings.SAMPLERATE
dropout = settings.DROPOUT
learning_rate = settings.LEARNING_RATE
embedding_size = settings.EMBEDDING_SIZE
embedding_input_size = settings.EMBEDDING_INPUT_SIZE
num_classes = settings.CLASS_COUNT

def broadcast(l, emb):
    sh = l.get_shape().as_list()[1]
    emb = emb[:, None, None, :]
    emb = tf.tile(emb, (1,sh,1,1))
    return tf.concat([l, emb], 3)


# Create model
def conv_net(x, cls, dropout, is_training=False):
    xs = tf.reshape(x, shape = [batch_size, sr, 1, 1] )

    conv1 = causal_GLU(xs, 4, [256, 1], scope='conv1', normalizer_fn=slim.batch_norm)
    pool1 = slim.max_pool2d(conv1, [2,1])
    pool1 = slim.dropout(pool1, is_training=is_training)
    print('conv1: ', pool1)

    with tf.name_scope('embedding'):
        with tf.variable_scope('embedding'):
            emb1 = embedding(cls, embedding_size, num_classes)
        embedded = broadcast(pool1, emb1)
        print('embedded:', embedded)

    #convblock 2
    conv2 = GLU(embedded, 16, [128, 1], scope='conv2')
    pool2 = slim.max_pool2d(conv2, [2,1])
    print('conv2: ', pool2)

    #convblock 3
    conv3 = GLU(pool2, 16, [128, 1], scope='conv3')
    conv3 = slim.dropout(conv3, is_training=is_training)
    print('conv3: ', conv3)

    #convblock 4
    conv4 = tf.depth_to_space(conv3, 4) #upconv
    print('d2sp: ', conv4)
    conv4 = tf.reshape(conv4, shape=[-1, sr, 1, 4]) # reshape upconvolution to have proper shape

    conv4 = GLU(conv4, 16, [128, 1], scope='conv4')
    print('conv4: ', conv4)

    #convblock 5
    conv5 = tf.concat([conv4, conv1], 3) # <- unet like concat first with last

    conv5 = GLU(conv5, 256, [1,1], scope='conv5')
    conv5 = slim.dropout(conv5, is_training=is_training)
    print('conv5: ', conv5)

    #out
    out = tf.reshape(conv5, [-1, sr, 256])
    print('out: ', out)
    return out

class Net:

    def __init__(self):
        # Store layers weight & bias
        pass


    def feedforward(self, x, y, frqid, keep_prob, cls, is_training=False):
        pred = conv_net(x, frqid, keep_prob, is_training)

        target_output = tf.reshape(y,[-1])
        prediction = tf.reshape(pred,[-1, discrete_class])

        # Define loss and optimizer
        with tf.name_scope('cost'):
            sparse = tf.nn.sparse_softmax_cross_entropy_with_logits(logits = prediction,
                                                                    labels = target_output)
            cost = tf.reduce_mean(sparse)

        correct_pred = tf.equal(tf.argmax(pred, 2), y)
        with tf.name_scope('accuracy'):
            accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

        return pred, cost, accuracy

    def train(self, **kwargs):
        self.train_x = kwargs['x']
        self.train_y = kwargs['y']

        self.train_pred, self.train_cost, self.train_acc = self.feedforward(is_training=True, **kwargs)
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
        gradients, variables = zip(*optimizer.compute_gradients(self.train_cost))
        gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
        self.optimizer = optimizer.apply_gradients(zip(gradients, variables))

    def validation(self, **kwargs):
        self.val_x = kwargs['x']
        self.val_y = kwargs['y']

        self.val_pred, self.val_cost, self.val_acc = self.feedforward(**kwargs)

    def begin(self, session):
        #session.run(self.init)
        pass

    def should_stop(self):
        return False
