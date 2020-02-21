import torch


def shift_left(matrix, dimension):
    m_len = matrix.size()[dimension]
    matrix.narrow(dim=dimension, start=0, length=m_len - 1) \
        .copy_(matrix.narrow(dim=dimension, start=1, length=m_len - 1))


def pad_tensor(tensor, seq_len):
    sz = list(tensor.size())
    sz[0] = seq_len - tensor.size()[0] % seq_len

    tail = tensor[-1].clone().expand(sz).to(tensor.device)
    tensor = torch.cat((tensor, tail))
    return tensor


def calc_attention_combination(attention_weights, matrix):
    return attention_weights.transpose(1, 2).matmul(matrix).squeeze(1)


def drop_matrix_rows_3d(matrix, forget_vector):
    return matrix.mul(forget_vector.unsqueeze(2))


def select_layered_hidden(layered_hidden, node_depths):
    batch_size = layered_hidden.size()[0]
    layers_num = layered_hidden.size()[1]
    hidden_size = layered_hidden.size()[2]
    depths_one_hot = layered_hidden.new(batch_size, layers_num)

    depths_one_hot.zero_().scatter_(1, node_depths.unsqueeze(1), 1)
    mask = depths_one_hot.unsqueeze(2).bool()
    mask = mask.to(layered_hidden.device)

    return torch.masked_select(layered_hidden, mask).view(batch_size, 1, hidden_size)


def set_layered_hidden(layered_hidden, node_depths, updated):
    batch_size = layered_hidden.size()[0]
    layers_num = layered_hidden.size()[1]
    hidden_size = layered_hidden.size()[2]

    node_depths_update = node_depths.unsqueeze(1).unsqueeze(2).expand(batch_size, 1, hidden_size)
    updated = updated.unsqueeze(1)
    node_depths_update.to(layered_hidden.device)

    return layered_hidden.scatter(1, node_depths_update, updated)


def create_one_hot(vector, one_hot_size):
    batch_size = vector.size()[0]
    depths_one_hot = vector.new(batch_size, one_hot_size)
    return depths_one_hot.zero_().scatter_(1, vector.unsqueeze(1), 1).float()
