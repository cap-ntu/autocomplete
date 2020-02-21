import torch
import time

from tensorboardX import SummaryWriter

if __name__ == '__main__':
    writer = SummaryWriter('/tensorboard/runs/test')

    for step in range(10):
        dummy_s1 = torch.rand(1)
        writer.add_scalar('data/random', dummy_s1, step)
        time.sleep(1)
