import time
import numpy as np
import tensorflow as tf
import pickle
from dataSet import ReadFromTFRecord, DataBatch, ImgShow
import matplotlib.pyplot as plt
import numpy
from numpy import cov
from numpy import trace
from numpy import iscomplexobj
from numpy import asarray
from numpy.random import shuffle
from scipy.linalg import sqrtm
from skimage.transform import resize
from numpy import asarray
from numpy import expand_dims
from numpy import log
from numpy import mean
from numpy import exp

def calculate_inception_score(p_yx, eps=1E-16):
    # calculate p(y)
    p_y = expand_dims(p_yx.mean(axis=0), 0)
    # kl divergence for each image
    kl_d = p_yx * (log(p_yx + eps) - log(p_y + eps))
    # sum over classes
    sum_kl_d = kl_d.sum(axis=1)
    # average over images
    avg_kl_d = mean(sum_kl_d)
    # undo the logs
    is_score = exp(avg_kl_d)
    return is_score

 
def scale_images(images, new_shape):
    images_list = list()
    for image in images:
        # resize with nearest neighbor interpolation
        new_image = resize(image, new_shape, 0)
        # store
        images_list.append(new_image)
    return asarray(images_list)
 
def batch_preprocess(data_batch):

    batch = sess.run(data_batch)
    
    batch_images = np.reshape(batch, [-1, 3, 32, 32]).transpose((0, 2, 3, 1))
    batch_images = batch_images * 2 - 1
    return  batch_images


def Dir():
    import os
    if not os.path.isdir('Wgan_ckpt'):
        os.mkdir('Wgan_ckpt')
    if not os.path.isdir('Wgan_trainLog'):
        os.mkdir('Wgan_trainLog')

real_shape = [-1,32,32,3]
data_total = 5000 
batch_size = 64 
noise_size = 128 
max_iters = 35000
learning_rate = 5e-5
CRITIC_NUM = 5
CLIP = [-0.1,0.1]

def GeNet(z, channel, is_train=True):

    with tf.variable_scope("generator", reuse=(not is_train)):

        layer1 = tf.layers.dense(z, 4 * 4 * 512)
        layer1 = tf.reshape(layer1, [-1, 4, 4, 512])
        layer1 = tf.layers.batch_normalization(layer1, training=is_train,)
        layer1 = tf.nn.relu(layer1)

        layer2 = tf.layers.conv2d_transpose(layer1, 256, 3, strides=2, padding='same',
                                            kernel_initializer=tf.random_normal_initializer(0, 0.02),
                                            bias_initializer=tf.random_normal_initializer(0, 0.02))
        layer2 = tf.layers.batch_normalization(layer2, training=is_train)
        layer2 = tf.nn.relu(layer2)

        layer3 = tf.layers.conv2d_transpose(layer2, 128, 3, strides=2, padding='same',
                                            kernel_initializer=tf.random_normal_initializer(0, 0.02),
                                            bias_initializer=tf.random_normal_initializer(0, 0.02))
        layer3 = tf.layers.batch_normalization(layer3, training=is_train)
        layer3 = tf.nn.relu(layer3)

        layer4 = tf.layers.conv2d_transpose(layer3, 64, 3, strides=2, padding='same',
                                            kernel_initializer=tf.random_normal_initializer(0, 0.02),
                                            bias_initializer=tf.random_normal_initializer(0, 0.02))
        layer4 = tf.layers.batch_normalization(layer4, training=is_train)
        layer4 = tf.nn.relu(layer4)

        logits = tf.layers.conv2d_transpose(layer4, channel, 3, strides=1, padding='same',
                                            kernel_initializer=tf.random_normal_initializer(0, 0.02),
                                            bias_initializer=tf.random_normal_initializer(0, 0.02))
        # outputs
        outputs = tf.tanh(logits)

        return logits,outputs


def DiNet(inputs_img, reuse=False, GAN = False,GP= False,alpha=0.2):

    with tf.variable_scope("discriminator", reuse=reuse):

        layer1 = tf.layers.conv2d(inputs_img, 128, 3, strides=2, padding='same')
        if GP is False:
            layer1 = tf.layers.batch_normalization(layer1, training=True)
        layer1 = tf.nn.leaky_relu(layer1,alpha=alpha)

        layer2 = tf.layers.conv2d(layer1, 256, 3, strides=2, padding='same')
        if GP is False:
            layer2 = tf.layers.batch_normalization(layer2, training=True)
        layer2 = tf.nn.leaky_relu(layer2, alpha=alpha)

        layer3 = tf.layers.conv2d(layer2, 512, 3, strides=2, padding='same')
        if GP is False:
            layer3 = tf.layers.batch_normalization(layer3, training=True)
        layer3 = tf.nn.leaky_relu(layer3, alpha=alpha)
        layer3 = tf.reshape(layer3, [-1, 4*4* 512])

        logits = tf.layers.dense(layer3, 1)

        if GAN:
            outputs = None
        else:
            outputs = tf.sigmoid(logits)

        return logits, outputs

#inputs
inputs_real = tf.placeholder(tf.float32, [None, real_shape[1], real_shape[2], real_shape[3]], name='inputs_real')
inputs_noise = tf.placeholder(tf.float32, [None, noise_size], name='inputs_noise')
_,g_outputs = GeNet(inputs_noise, real_shape[3], is_train=True)
_,g_test = GeNet(inputs_noise, real_shape[3], is_train=False)

d_logits_real, _ = DiNet(inputs_real,GAN=True)
d_logits_fake, _ = DiNet(g_outputs,GAN=True,reuse=True)

#-original loss function
g_loss = tf.reduce_mean(-d_logits_fake)

d_loss = tf.reduce_mean(d_logits_fake - d_logits_real)


train_vars = tf.trainable_variables()
g_vars = [var for var in train_vars if var.name.startswith("generator")]
d_vars = [var for var in train_vars if var.name.startswith("discriminator")]

# Optimizer
with tf.control_dependencies(tf.get_collection(tf.GraphKeys.UPDATE_OPS)):
    g_train_opt = tf.train.RMSPropOptimizer(learning_rate).minimize(g_loss, var_list=g_vars)
    d_train_opt = tf.train.RMSPropOptimizer(learning_rate).minimize(d_loss, var_list=d_vars)

# clip
d_clip_opt = [tf.assign(var, tf.clip_by_value(var, CLIP[0], CLIP[1])) for var in d_vars]

# read TFR
[data,label] = ReadFromTFRecord(sameName= r'./TFR/class1-*',isShuffle= False,datatype= tf.float64,
                                labeltype= tf.int64,isMultithreading= True)

[data_batch,label_batch] = DataBatch(data,label,dataSize= 32*32*3,labelSize= 1,
                                                   isShuffle= True,batchSize= 64)
# save
GenLog = []
losses = []
saver = tf.train.Saver(var_list=[var for var in tf.trainable_variables()
                                 if var.name.startswith("generator")],max_to_keep=5)

with tf.Session() as sess:

    Dir()

    init = (tf.global_variables_initializer(), tf.local_variables_initializer())
    sess.run(init)

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)
    
    time_start = time.time() # start timing
    for steps in range(max_iters):
        steps += 1

        if steps < 25 or steps % 500 == 0:
            critic_num = 100
        else:
            critic_num = CRITIC_NUM

        for i in range(CRITIC_NUM):
            batch_images = batch_preprocess(data_batch)  # images
            batch_noise = np.random.normal(size=(batch_size, noise_size))  # noise(normal)
            _ = sess.run(d_train_opt, feed_dict={inputs_real: batch_images,
                                                 inputs_noise: batch_noise})
            sess.run(d_clip_opt)

        batch_images = batch_preprocess(data_batch)  # images
        batch_noise = np.random.normal(size=(batch_size, noise_size))  # noise(normal)
        _ = sess.run(g_train_opt, feed_dict={inputs_real: batch_images,
                                             inputs_noise: batch_noise})

        if steps % 5 == 1:

            train_loss_d = d_loss.eval({inputs_real: batch_images,
                                        inputs_noise: batch_noise})
            train_loss_g = g_loss.eval({inputs_real: batch_images,
                                        inputs_noise: batch_noise})
            losses.append([train_loss_d, train_loss_g,steps])


            batch_noise = np.random.normal(size=(batch_size, noise_size))
            gen_samples = sess.run(g_test, feed_dict={inputs_noise: batch_noise})
            genLog = (gen_samples[0:11] + 1) / 2
            GenLog.append(genLog)


            print('step {}...'.format(steps),
                  "Discriminator Loss: {:.4f}...".format(train_loss_d),
                  "Generator Loss: {:.4f}...".format(train_loss_g))

        if steps % 500 ==0:
            saver.save(sess, './Wgan_ckpt/generator.ckpt', global_step=steps)

    coord.request_stop()
    coord.join(threads)
    
#end timing
time_end = time.time()
print('Finished! Time：%.2f s.'%(time_end-time_start))

# Save info
with open('./Wgan_trainLog/loss_variation.loss', 'wb') as l:
    losses = np.array(losses)
    pickle.dump(losses,l)
    print('Saving loss info...')


with open('./Wgan_trainLog/GenLog.log', 'wb') as g:
    pickle.dump(GenLog, g)
    print('Saving GenLog inof..')
    
with open('./Wgan_trainLog/loss_variation.loss', 'wb') as l:
    losses = np.array(losses)
    pickle.dump(losses,l)
    print('loss saved')

with open('./Wgan_trainLog/GenLog.log', 'wb') as g:
    pickle.dump(GenLog, g)
    print('GenLog saved..')

#output
with open('./Wgan_trainLog/GenLog.log', 'rb') as f:

    GenLog = pickle.load(f)
    GenLog = np.array(GenLog)
    ImgShow(GenLog,[-1],10)

with open(r'./Wgan_trainLog/loss_variation.loss','rb') as l:
    losses = pickle.load(l)
    fig, ax = plt.subplots(figsize=(20, 7))
    plt.plot(losses.T[2],losses.T[0], label='Discriminator  Loss')
    plt.plot(losses.T[2],losses.T[1], label='Generator Loss')
    plt.title("Training Losses")
    plt.xlabel('iterations')
    plt.ylabel('loss')
    plt.legend()
    plt.show()

with tf.Session() as sess:

    meta_graph = tf.train.import_meta_graph('./Wgan_ckpt/generator.ckpt-35000.meta')
    meta_graph.restore(sess,tf.train.latest_checkpoint('./Wgan_ckpt'))
    graph = tf.get_default_graph()
    inputs_noise = graph.get_tensor_by_name("inputs_noise:0")
    d_outputs_fake = graph.get_tensor_by_name("generator/Tanh:0")
    sample_noise= np.random.normal(size=(10, 128))
    gen_samples = sess.run(d_outputs_fake,feed_dict={inputs_noise: sample_noise})
    gen_samples = [(gen_samples[0:11]+1)/2]
    ImgShow(gen_samples, [0], 10)
    for i in range(10):
        img=gen_samples[0][i]
        plt.imshow(img)
        plt.axis('off')
        plt.savefig("wgan_img/car_%d.png" % i)
        plt.show
