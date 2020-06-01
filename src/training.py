import torch
from torch import nn 
import torch.nn.functional as F
import time
from pathlib import Path
import datetime

import visualize
import models

from util import Constants
from util import Objects

import progressbar


def model_wrapper(model, x, label_str=None): 
    yh = model(x)
    predictions = torch.argmax(yh, dim=1)

    if label_str:
        if not label_str == "":
            label_str = "_" + label_str
        print("    x{}.size(): {}".format(label_str, x.size()))   
        print("    yh{}.size(): {}".format(label_str, yh.size()))
        print("    predictions.size(): {}".format(predictions.size()))
    return yh, predictions


def run_batch(model, loss_func, x_batch, y_batch, optimizer=None, verbose=False):
    yh_batch, predictions = model_wrapper(model, x_batch)

    accuracy = (predictions == y_batch).float().mean()
    loss = loss_func(yh_batch, y_batch)

    if optimizer: # perform learning
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return accuracy, loss.item()


def run_epoch_2(model, loss_func, dataloader, 
    epoch=None, bar=None, optimizer=None, verbose=False, fast=False):

    running_loss, running_accuracy = 0.0, 0.0
    epoch_len = len(dataloader)*Constants.batch_size

    if optimizer: # perform learning
        optimizer.zero_grad()
    for i, (x_batch, y_batch) in enumerate(dataloader):
        if i > 10 and fast:
            break
        accuracy, loss = run_batch(
            model, loss_func, x_batch, y_batch, optimizer, verbose)
        running_accuracy += accuracy
        running_loss += loss

        if bar and epoch:
            bar.update(epoch*epoch_len + i*Constants.batch_size)

    epoch_accuracy, epoch_loss = \
        running_accuracy/len(dataloader), running_loss/len(dataloader)
    
    # if validation_dataloader:
    #     epoch_validation_accuracy, epoch_validation_loss = \
    #         run_epoch(model, loss_func, validation_dataloader)

    # if training_stats_arr:
    #     training_stats_arr[-1]["loss"] = epoch_loss
    #     training_stats_arr[-1]["accuracy"] = epoch_accuracy
    #     training_stats_arr.append({"loss": None, "accuracy": None,
    #         "validation_loss": epoch_validation_loss, 
    #         "validation_accuracy": epoch_validation_accuracy.item()
    #         })

    #     print("    Epoch {}: train acc {}, val acc {} || train loss {}, val loss {}.".format(
    #         len(training_stats_arr)-1,
    #         training_stats_arr[-2]["accuracy"], 
    #         training_stats_arr[-2]["validation_accuracy"], 
    #         training_stats_arr[-2]["loss"], 
    #         training_stats_arr[-2]["validation_loss"]), 
    #         file = open(Path(__file__).parent.parent / 
    #             "logs" / '{}.txt'.format(Constants.save_str), 'a'))

    return epoch_accuracy, epoch_loss


def run_epoch(model, loss_func, dataloader, 
    bar=None, optimizer=None, validation_dataloader=None, 
    training_stats_arr=None, verbose=False, fast=False):

    running_loss, running_accuracy = 0.0, 0.0
    epoch_len = len(dataloader)*Constants.batch_size

    for i, (x_batch, y_batch) in enumerate(dataloader):
        if i > 10 and fast:
            break
        accuracy, loss = run_batch(
            model, loss_func, x_batch, y_batch, optimizer, verbose)
        running_accuracy += accuracy
        running_loss += loss

        if bar:
            bar.update((len(training_stats_arr)-1)*epoch_len + i*Constants.batch_size)

    epoch_accuracy, epoch_loss = \
        running_accuracy/len(dataloader), running_loss/len(dataloader)
    
    if validation_dataloader:
        epoch_validation_accuracy, epoch_validation_loss = \
            run_epoch(model, loss_func, validation_dataloader)

    if training_stats_arr:
        training_stats_arr[-1]["loss"] = epoch_loss
        training_stats_arr[-1]["accuracy"] = epoch_accuracy
        training_stats_arr.append({"loss": None, "accuracy": None,
            "validation_loss": epoch_validation_loss, 
            "validation_accuracy": epoch_validation_accuracy.item()
            })

        print("    Epoch {}: train acc {}, val acc {} || train loss {}, val loss {}.".format(
            len(training_stats_arr)-1,
            training_stats_arr[-2]["accuracy"], 
            training_stats_arr[-2]["validation_accuracy"], 
            training_stats_arr[-2]["loss"], 
            training_stats_arr[-2]["validation_loss"]), 
            file = open(Path(__file__).parent.parent / 
                "logs" / '{}.txt'.format(Constants.save_str), 'a'))

    return epoch_accuracy, epoch_loss


# class Optimizers:

#     def __init__(self, model):
#         self.model = model

#     sgd = torch.optim.SGD(self.model.parameters(), lr=Constants.learning_rate)
#     sgd_decay = torch.optim.SGD(self.model.parameters(), lr=0.1, weight_decay=5e-4)
#     adam = torch.optim.Adam(self.model.parameters(), lr=Constants.learning_rate)

def init_optimizer(model, optimizer_str="adam"):
    if optimizer_str == "sgd":
        return torch.optim.SGD(model.parameters(), lr=Constants.learning_rate)
    if optimizer_str == "adam":
        return torch.optim.Adam(model.parameters(), lr=Constants.learning_rate)
    if optimizer_str == "sgd_decay":
        return torch.optim.SGD(model.parameters(), lr=0.1, weight_decay=5e-4)
    raise Exception("Invalid optimizer specification of {}.".format(optimizer_str))

class Models:
    in_channels = 784 if Constants.dataset_str == "mnist" else 3072

    linear = models.Linear(in_channels, Constants.out_channels).to(Objects.dev)
    small_nn = models.SmallNN(in_channels, Constants.out_channels).to(Objects.dev)
    large_nn = models.LargeNN(in_channels, Constants.out_channels).to(Objects.dev)
    small_cnn = models.SmallCNN(Constants.out_channels).to(Objects.dev)
    best_cnn = models.BestCNN(Constants.out_channels).to(Objects.dev)


def save_model(model, optimizer, loss, save_str, epoch):
    torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(), 
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': loss
        }, Path("models") / save_str)


def load_model(path, model, optimizer=None):
    saved_model_dict = torch.load(path)
    model.load_state_dict(saved_model_dict['model_state_dict'])
    if optimizer:
        optimizer.load_state_dict(saved_model_dict['optimizer_state_dict'])
    epoch = saved_model_dict['epoch']
    loss = saved_model_dict['loss']

    return model, optimizer, epoch, loss


# helpers for testing ===================================================================================
# =======================================================================================================

def test():
    model = getattr(Models, "best_cnn")
    optimizer = init_optimizer(model, "adam")
    print(optimizer)
    print(type(optimizer))

if __name__ == "__main__":
    test()
