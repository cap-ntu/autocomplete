import torch

def topk_hits(prediction, target):
    n = prediction.size()[0]
    k = prediction.size()[1]

    hits = torch.zeros(k, dtype=torch.int64)
    correct = prediction.eq(target.unsqueeze(1).expand_as(prediction))
    for tk in range(k):
        cur_hits = correct[:, :tk + 1]
        hits[tk] += cur_hits.sum()

    return hits, n

def indexed_topk_hits(prediction, target, index):
    selected_prediction = torch.index_select(prediction, 0, index)
    selected_target = torch.index_select(target, 0, index)

    if selected_prediction.size()[0] == 0:
        return torch.zeros((prediction.size()[-1]), dtype=torch.int64), 0
    return topk_hits(selected_prediction, selected_target)