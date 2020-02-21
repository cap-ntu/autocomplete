import torch
import torch.nn as nn
import torch.nn.functional as F

from autocomplete.lib.calculation import drop_matrix_rows_3d, calc_attention_combination
from autocomplete.lib.core import BaseModule
from autocomplete.lib.utils import init_layers_uniform, get_best_device


class CyclicBuffer:
    def __init__(self, buffer):
        self.buffer = buffer
        self.it = 0

    def add_vector(self, vector):
        self.buffer[:, self.it, :].copy_(vector)
        self.it += 1
        if self.it >= self.buffer.size()[1]:
            self.it = 0

    def get(self):
        return self.buffer


class LastKBuffer:
    def __init__(self, window_len, buffer):
        assert window_len <= buffer.size()[1]
        self.buffer_size = buffer.size()[1]
        self.window_len = window_len
        self.buffer = buffer

        self.it = window_len

    def add_vector(self, vector):
        self.buffer[:, self.it, :].copy_(vector.detach()) 
        self.it += 1
        if self.it >= self.buffer_size:
            self.buffer.narrow(dim=1, start=0, length=self.window_len).copy_(
                self.buffer.narrow(dim=1, start=self.buffer_size - self.window_len, length=self.window_len)
            )
            self.it = self.window_len

    def get(self):
        return self.buffer.narrow(dim=1, start=self.it - self.window_len, length=self.window_len)


class Attn(BaseModule):
    def __init__(self, method, hidden_size):
        super(Attn, self).__init__()

        self.method = method
        self.hidden_size = hidden_size

        if self.method == 'general':
            self.attn = nn.Linear(self.hidden_size, self.hidden_size)
            init_layers_uniform(-0.05, 0.05, [self.attn])


    def forward(self, main_vector, attn_vectors):
        seq_len = attn_vectors.size()[1]
        attn_energies = self.score(main_vector, attn_vectors)
        return F.softmax(attn_energies, dim=1)

    def score(self, main_vector, attn_vectors):
        if self.method == 'dot':
            pass  
        elif self.method == 'general':
            attn_vectors = self.attn(attn_vectors)
        else:
            raise Exception('Unknown attention method: {}'.format(self.method))

        main_vector = main_vector.unsqueeze(1).unsqueeze(1)
        attn_vectors = attn_vectors.unsqueeze(3)
        energy = main_vector.matmul(attn_vectors).squeeze(-1)
        return energy


class ContextAttention(BaseModule):
    def __init__(self, context_len, hidden_size):
        super().__init__()
        self.seq_len = context_len
        self.hidden_size = hidden_size
        self.it = 0
        self.attn = Attn(method='general', hidden_size=self.hidden_size)
        self.context_buffer = None

    def init_hidden(self, batch_size):
        b_matrix = torch.FloatTensor(batch_size, 2 * self.seq_len, self.hidden_size).to(get_best_device())
        self.context_buffer = LastKBuffer(window_len=self.seq_len, buffer=b_matrix)

    def forget_context_partly(self, forget_vector):
        drop_matrix_rows_3d(self.context_buffer.get(), forget_vector)

    def forward(self, h_t):
        assert self.context_buffer is not None

        current_context = self.context_buffer.get()
        attn_weights = self.attn(h_t, current_context)
        cntx = calc_attention_combination(attn_weights, current_context)
        self.context_buffer.add_vector(h_t)
        return cntx
