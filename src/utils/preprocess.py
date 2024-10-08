import pandas as pd
import networkx as nx
import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.transforms import RandomLinkSplit
from torch_geometric.utils import index_to_mask
import pickle


def preprocess_graph(G):
    # n_nodes, n_edges = G.number_of_nodes(), G.number_of_edges()
    
    sorted_nodes = sorted(list(G.nodes()))
    
    user_node2num = {v: i for i, v in enumerate(sorted_nodes) if 'user' in G.nodes[v]['type']}
    item_node2num = {v: i for i, v in enumerate(sorted_nodes) if 'book' in G.nodes[v]['type']}
    n_user, n_item = len(user_node2num), len(item_node2num)

    new_user_idx = [i for i in range (n_user)]
    new_item_idx = [i+n_user for i in range (n_item)]

    id2idx = dict(zip([k for k, v in user_node2num.items()], new_user_idx))
    temp = dict(zip([k for k, v in item_node2num.items()], new_item_idx))
    id2idx.update(temp)

    G = nx.relabel_nodes(G, id2idx)

    idx2id = {v:k for k,v in id2idx.items()}

    # with open('id2idx.pickle','wb') as fw:
    #     pickle.dump(id2idx, fw)
    
    # print(n_user, n_item) # 11842 5896

    return G, new_user_idx, new_item_idx, n_user, n_item, idx2id


def make_data(G):
    num_nodes = G.number_of_nodes() # 17738 = 11842 + 5896
    num_edges = G.number_of_edges() # 767616
    print(num_nodes, num_edges) # 17738 767616

    edge_idx = torch.Tensor(np.array(G.edges()).T) # torch.Size([2, 767616]) = [2, n_edges]
    graph_data = Data(edge_index = edge_idx, num_nodes = num_nodes)

    # convert to train/val/test splits
    transform = RandomLinkSplit(
        is_undirected=True, 
        add_negative_train_samples=False, 
        neg_sampling_ratio=0,
        num_val=0.15, num_test=0.15
    )
    train_split, val_split, test_split = transform(graph_data)

    # It was hard to understand for me... refer to https://github.com/pyg-team/pytorch_geometric/discussions/5189#discussioncomment-3378727 :)

    # Edge index: message passing edges
    # : testing edges (not the real edges)
    train_split.edge_index = train_split.edge_index.type(torch.int64)
    val_split.edge_index = val_split.edge_index.type(torch.int64)
    test_split.edge_index = test_split.edge_index.type(torch.int64)

    # Edge label index: supervision edges
    # : ground truth edges
    train_split.edge_label_index = train_split.edge_label_index.type(torch.int64)
    val_split.edge_label_index = val_split.edge_label_index.type(torch.int64)
    test_split.edge_label_index = test_split.edge_label_index.type(torch.int64)

    return train_split, val_split, test_split
