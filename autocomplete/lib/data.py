from abc import abstractmethod

import numpy as np
import torch
from tqdm import tqdm

from autocomplete.lib.utils import get_best_device


def split_train_validation(data, split_coefficient):
    train_examples = int(len(data) * split_coefficient)
    return data[:train_examples], data[train_examples:len(data)]


def get_shuffled_indexes(length):
    temp = np.arange(length)
    np.random.shuffle(temp)
    return temp


def get_random_index(length):
    return np.random.randint(length)


class DataReader:
    def __init__(self):
        self.train_data = []
        self.validation_data = []
        self.eval_data = []
        self.eval_tails = 0


class DataGenerator:

    @abstractmethod
    def get_train_generator(self):
        pass

    @abstractmethod
    def get_validation_generator(self):
        pass

    @abstractmethod
    def get_eval_generator(self):
        pass


class DataChunk:

    @abstractmethod
    def prepare_data(self, seq_len):
        pass

    @abstractmethod
    def get_by_index(self, index):
        pass

    @abstractmethod
    def size(self):
        pass


class DataChunksPool:
    def __init__(self, chunks, splits=1, shuffle=True):
        self.chunks = chunks
        self.splits = splits
        self.shuffle = shuffle
        self.epoch_size = len(self.chunks) // self.splits

        self.current = 0
        self.right = 0
        self._recreate_indexes()

    def start_epoch(self):
        if self.current != self.right:
            raise Exception(
                'You should finish previous epoch first, cur: {}, right: {}'.format(self.current, self.right)
            )

        if self.current + self.epoch_size > len(self.chunks): 
            self.current = 0
            self._recreate_indexes()

        self.right = min(self.current + self.epoch_size, len(self.chunks))

    def get_chunk(self):
        if self.current == self.right:
            return None
        else:
            cur = self.current
            self.current += 1

            if self.current % 100 == 0:
                print('Processed {} programs'.format(self.current))

            return self.chunks[self.indexes[cur]]

    def is_epoch_finished(self):
        return self.current == self.right

    def _recreate_indexes(self):
        if self.shuffle:
            self.indexes = get_shuffled_indexes(length=len(self.chunks))
        else:
            self.indexes = np.arange(start=0, stop=len(self.chunks))


class DataBucket:
    def __init__(self, pool: DataChunksPool, seq_len, on_new_chunk=None):
        self.pool = pool
        self.seq_len = seq_len
        self.on_new_chunk = on_new_chunk

        self.chunk = None
        self.index = 0

    def get_next_index_with_chunk(self):
        if self.is_empty():
            print('Chunk: {}, Index: {}'.format(self.chunk, self.index))
            raise Exception('No data in bucket')

        if (self.index == 0) and (self.on_new_chunk is not None):
            self.on_new_chunk()

        start = self.index
        chunk = self.chunk

        self.index += self.seq_len
        self.refill_if_necessary()

        return start, chunk

    def is_empty(self):
        return (self.chunk is None) or (self.chunk.size() == self.index)

    def refill_if_necessary(self):
        if self.is_empty():
            self.chunk = self.pool.get_chunk()
            self.index = 0


class BucketsBatch:
    def __init__(self, pool: DataChunksPool, seq_len, batch_size):
        self.pool = pool
        self.seq_len = seq_len
        self.batch_size = batch_size
        self.buckets = []

        self.forget_vector = torch.FloatTensor(batch_size, 1).to(get_best_device())

        def forget(x):
            self.forget_vector[x] = 0

        def get_forget(x):
            return lambda: forget(x)

        for i in range(self.batch_size):
            self.buckets.append(
                DataBucket(
                    pool=self.pool,
                    seq_len=self.seq_len,
                    on_new_chunk=get_forget(i)
                ))

    def get_epoch(self, retriever):
        self.pool.start_epoch()

        for b in self.buckets:
            b.refill_if_necessary()

        while True:
            self.forget_vector.fill_(1)
            yield retriever(self.buckets), self.forget_vector
            if self.pool.is_epoch_finished():
                should_exit = False
                for b in self.buckets:
                    if b.chunk is None:
                        should_exit = True
                if should_exit:
                    break


class BatchedDataGenerator(DataGenerator):
    def __init__(self, data_reader, seq_len, batch_size, shuffle=True):
        super(BatchedDataGenerator, self).__init__()
        self.data_reader = data_reader
        self.seq_len = seq_len
        self.batch_size = batch_size

        self.batches = {}

        if data_reader.train_data is not None:
            self.train_pool = self._prepare_data_(data_reader.train_data, splits=1, shuffle=shuffle)
            self.train_batcher = BucketsBatch(self.train_pool, self.seq_len, self.batch_size)

        if data_reader.validation_data is not None:
            self.validation_pool = self._prepare_data_(data_reader.validation_data, splits=1, shuffle=shuffle)
            self.validation_batcher = BucketsBatch(self.validation_pool, self.seq_len, self.batch_size)

        if data_reader.eval_data is not None:
            self.eval_pool = self._prepare_data_(data_reader.eval_data, splits=1, shuffle=True)
            self.eval_batcher = BucketsBatch(self.eval_pool, self.seq_len, self.batch_size)

    @abstractmethod
    def _retrieve_batch(self, key, buckets):
        pass

    def _get_batched_epoch(self, key, batcher):
        return batcher.get_epoch(retriever=lambda buckets: self._retrieve_batch(key, buckets))

    def get_train_generator(self):
        return self._get_batched_epoch('train', self.train_batcher)

    def get_validation_generator(self):
        return self._get_batched_epoch('validation', self.validation_batcher)

    def get_eval_generator(self):
        return self._get_batched_epoch('eval', self.eval_batcher)

    def _prepare_data_(self, data, splits=5, shuffle=True):
        for i in tqdm(range(len(data))):
            data[i].prepare_data(self.seq_len)

        return DataChunksPool(chunks=data, splits=splits, shuffle=shuffle)
