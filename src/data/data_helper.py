# -*- coding: utf-8 -*-
"""data_helper.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oyV5FER0-cP3Hw8heSp5KwHhGmAsopPP
"""

import numpy as np 
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from PIL import Image

# helper function to downsample the marjority in dataframe:
# input a dataframe and the size for the marjority
# output a dataframe with downsample marjority
def undersample(df, count, rs=42):
  '''Take a dataframe and numer
    Return a dataframe that downsample the majority to match the input number
  '''
  result=[]
  df_group = df.groupby('dx')
  for x in df['dx'].unique():
    group = df_group.get_group(x)
    num = int(group['dx'].value_counts())
    if num >= count:
      s=group.sample(count, axis=0, random_state=rs)
    else:
      s=group.sample(frac=1, axis=0, random_state=rs)
    result.append(s)
  return pd.concat(result, axis=0).reset_index(drop=True)

# helper function to increase the sample for the minority in dataframe:
# input a dataframe and the size for the minority
# output a dataframe with oversampled minority
def oversample(df, count, rs=42):
  '''Take a dataframe and numer
    Return a dataframe that oversample the minorities to match the input number
  '''
  lst = [df]
  for class_index, group in df.groupby('dx'):
      lst.append(group.sample(count-len(group), replace=True, random_state=rs))
  df_new = pd.concat(lst)
  return df_new

# helper function to convert the image_id into image data in dataframe:
# input a dataframe, the image path, the image height and width
# output a dataframe with image data
def img_np_convert(df, image_path, h, w):
  '''Take a dataframe, the image stored path, the height of image and the width
    of image
    Return a dataframe with the image data convert from image ID
  '''
  df['image_id'] = image_path + df['image_id'] +'.jpg'
  df['image'] = df['image_id'].map(lambda x: np.asarray(Image.open(x).resize((h, w))).astype(np.float32))
  return df

# helper function to convert the image_id into image data in dataframe:
# input a dataframe, the image path, the image height and width
# output a dataframe with image data with normalize pixels
def img_np_convert_scaled(df, image_path, h, w):
  '''Take a dataframe, the image stored path, the height of image and the width
    of image
    Return a dataframe with the normalized image data convert from image ID
  '''
  df['image_id'] = image_path + df['image_id'] +'.jpg'
  df['image'] = df['image_id'].map(lambda x: (np.asarray(Image.open(x).resize((h, w)))/255).astype(np.float32))
  return df

# helper function to split the dataframe into train and test
# input dataframe, train size, test size
# output the train dataframe, test dataframe
def my_split(df, train_size, test_size, rs=42):
  '''Take a dataframe, the train size and the test size
    Return two dataframes that split from original dataframe and by the given train
    test size 
  '''
  df_train, df_test = train_test_split(df, test_size=test_size, shuffle=True, random_state=rs)

  df_train.reset_index(inplace=True)
  df_test.reset_index(inplace=True)
  return df_train, df_test

# helper function to calculate weight base on population proportion
# input the dataframe
# output the dictionary for class weight and labels
def weight_cal(df):
  '''Take a dataframe
    Return a dictionary for class weight and labels
  '''
  class_weight={}
  labels = list(df['dx'].unique())
  labels.sort()
  count = df['dx'].value_counts()
  for idx in range(7):
    class_weight[idx] = count['nv']/count[labels[idx]]
  return class_weight, labels

# helper function to convert data in dataframe to numpy for training and test
# for CNN
def df_to_np1(df):
  '''Take a dataframe
    Return a numpy for image data, a numpy for data other than image and a numpy
    for labels
  '''
  image = np.asarray(df['image'].to_list())

  df_feature = df.iloc[:, 3:-1]
  c_feature = df_feature.loc[:, ~df_feature.columns.isin(['sex', 'dx'])].to_numpy()

  target_df = df['dx']
  target = pd.get_dummies(data=target_df, columns=['dx']).to_numpy()
  return image, c_feature, target

# helper function to convert data in dataframe to numpy for training and test
# for sklearn model and DNN
def df_to_np2(df):
  '''Take a dataframe
    Return a numpy for feature data and a numpy for labels
  '''
  df['image'] = df['image'].map(lambda x : x.flatten())
  i_feature = np.asarray(df['image'].tolist())
  df_feature = df.iloc[:, 3:-1]
  c_feature = df_feature.loc[:, ~df_feature.columns.isin(['sex', 'dx'])].to_numpy()
  features = np.concatenate((i_feature, c_feature), axis=1)
  
  target_df = df['dx']
  target = pd.get_dummies(data=target_df, columns=['dx']).to_numpy()
  return features, target

# helper function to augment the image by rotate and translate
def image_augment(df, target, count, size, rs=42):
  '''Take a dataframe, a list of labels, a number for sample and another for size
    Return a dataframe with the list of labels being augment by count*size
  '''
  df_group = df.groupby('dx')
  group = df_group.get_group(target)
  s=group.sample(count, axis=0, random_state=rs)

  datagen = ImageDataGenerator(
    rotation_range = 20,
    width_shift_range = 0.1,
    height_shift_range = 0.1,
    horizontal_flip = True,
    fill_mode='nearest')
  
  for index, row in s.iterrows():
    image = row['image'].reshape((1, ) + row['image'].shape)
    gen = datagen.flow(image, batch_size=size)
    input = row.to_list()
    for i in range(size):
      img = next(gen)
      input[-1] = img[0]
      df.loc[len(df.index)] = input
  return None

# combine helper functions for keras CNN
def prep_pipeline1(df_o, image_path, upper_size, h, w, aug_targets, aug_count, aug_size, rs=42):
  '''Take a dataframe, image data path, image height, image width, list of labels,
    the sample to augment, and the size to augment
    Return a train data set, a test data set, a dictionary for weight and labels
  '''
  df_o = pd.get_dummies(data=df_o, columns=['dx_type', 'localization'])
  df_u = undersample(df_o, upper_size)
  df_u['age'].fillna(value=int(df_u['age'].mean()), inplace=True)
  df_u['age'] = df_u['age'].astype(np.float32)
  
  df = img_np_convert(df_u, image_path, h, w)

  df_train, df_test = my_split(df, 0.7, 0.3, rs)

  for target in aug_targets:
    image_augment(df_train, target, aug_count, aug_size, rs)

  weight, labels = weight_cal(df_train)

  X_train_i, X_train_c, y_train = df_to_np1(df_train)
  X_test_i, X_test_c, y_test = df_to_np1(df_test)
  return (X_train_i, X_train_c, y_train), (X_test_i, X_test_c, y_test), weight, labels

# combine helper functions for sklearn model and dnn
def prep_pipeline2(df_o, image_path, upper_size, h, w, aug_targets, aug_count, aug_size, rs=42):
  '''Take a dataframe, image data path, image height, image width, list of labels,
    the sample to augment, and the size to augment
    Return a train data set, a test data set, a dictionary for weight and labels
  '''
  df_o = pd.get_dummies(data=df_o, columns=['dx_type', 'localization'])
  df_u = undersample(df_o, upper_size)
  df_u['age'].fillna(value=int(df_u['age'].mean()), inplace=True)
  df_u['age'] = df_u['age'].astype(np.float32)

  df = img_np_convert_scaled(df_u, image_path, h, w)

  df_train, df_test = my_split(df, 0.7, 0.3, rs)

  for target in aug_targets:
    image_augment(df_train, target, aug_count, aug_size, rs)

  weight, labels = weight_cal(df_train)

  X_train, y_train = df_to_np2(df_train)
  X_test, y_test = df_to_np2(df_test)
  return (X_train, y_train), (X_test, y_test), weight, labels