# Overview

Using the car pictures in cifar10 dataset to build DCGAN and WGAN for generating car pictures.

[//]: # (Image References)

[image1]: ./pictures/carcifardata.png

[image2]: ./pictures/loss_wgan.png

[image3]: ./pictures/loss_dcgan.png

[image4]: ./pictures/dcgan_last.png

[image5]: ./pictures/wgan_last.png

## Requirement

* tensorflow 1.15
* python 3.6 
* cifar10 dataset

for `dataSet.py`, it is for getting the training data, save as TFRecords.

you can change the class # in `dataSet.py` to get different data from cifar10 dataset.

## Details About How to Play

* run

```sh
DCGAN.py
```
for DCGAN model


* run

```sh
WGAN.py
```
for WGAN model

# WGAN model.

`WGAN.py`

* Total data number 	5000

* Batch size	64

* Noise size	128

* Iterations	35000

* Learning rate	0.00005



# DCGAN model.

`DCGAN.py`

* Total data number 	5000

* Batch size	64

* Noise size	128

* Iterations	10000

* Learning rate	0.0002

 `TFR` foder is the training data.

`best_10_images_for_all` is the foder of the best 10 images generated either by WGAN or DCGAN.

`dcgan_best_pic` and `wgan_best_pic` are the foders for seperate the images for DCGAN and WGAN. There are 10 images for each model.

# Visulize the training data from cifar10

![alt text][image1]

# The loss curve of WGAN

![alt text][image2]

# The loss curve of DCGAN 

![alt text][image3]

# The last 10 car images generated by DCGAN

![alt text][image4]

# The last 10 car images generated by the WGAN

![alt text][image5]

