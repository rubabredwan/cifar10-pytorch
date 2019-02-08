import argparse
import os
import time

import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.optim
import torch.utils.data
import torchvision.transforms as transforms
import torchvision.datasets as datasets
import resnet

epochs = 10
start_epoch = 0
batch_size = 128
lr = 0.1
momentum = 0.9
print_freq = 20
weight_decay = 0.0001

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)

model = resnet.resnet20()
model = model.to(device)

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])

train_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10(root='./data', train=True, transform=transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, 4),
        transforms.ToTensor(),
        normalize,
    ]), download=True),
    batch_size=batch_size, shuffle=True,
    num_workers=4)

val_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10(root='./data', train=False, transform=transforms.Compose([
        transforms.ToTensor(),
        normalize,
    ])),
    batch_size=batch_size, shuffle=False,
    num_workers=4)

criterion = nn.CrossEntropyLoss()


optimizer = torch.optim.SGD(model.parameters(), lr=lr,
                            momentum=momentum,
                            weight_decay=weight_decay)

lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, 
                                                    milestones=[100, 150], 
                                                    last_epoch=-1)

PATH = 'pretrained/'

history = {'acc': [], 'loss': [], 'val_acc': [], 'val_loss': []}

def train():
    model.train()

    running_loss = 0
    correct = 0
    total = 0

    start = time.time()
    for i, (images, labels) in enumerate(train_loader):

        images = images.to(device)
        labels = labels.to(device)

        output = model(images)
        loss = criterion(output, labels)
        _, predicted = torch.max(output.data, 1)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    return correct/total * 100, running_loss / 50000 * 128 

def validate():
    model.eval()

    running_loss = 0
    correct = 0
    total = 0
    start = time.time()
    
    for i, (images, labels) in enumerate(val_loader):

        images = images.to(device)
        labels = labels.to(device)

        output = model(images)
        loss = criterion(output, labels)
        _, predicted = torch.max(output.data, 1)

        running_loss += loss.item()
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    return correct / total * 100, running_loss / 10000 * 128

for epoch in range(0, epochs):
    start = time.time()
    acc, loss = train()
    val_acc, val_loss = validate()

    print('Epoch %d/%d' % (epoch + 1, epochs))
    print('%.2f - loss: %.4f - acc: %.2f - val_loss: %.4f - val_acc: %.2f' % (
        time.time() - start,
        loss, acc, val_loss, val_acc))


    history['acc'] += [acc]
    history['loss'] += [loss]
    history['val_acc'] += [val_acc]
    history['val_loss'] += [val_loss]

    lr_scheduler.step()

torch.save({
    'epoch': epochs,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'history':history
    }, 'resnet20.pth')

