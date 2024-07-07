import torch

checkpoint_path = '/home/artorius/projects/access-simplification/resources/models/best_model/checkpoints/checkpoint_best.pt'
checkpoint = torch.load(checkpoint_path)
print(f"Checkpoint {checkpoint['args']}")