import os
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
from sklearn.metrics import classification_report
from sklearn.metrics import precision_recall_fscore_support
import torch.nn as nn
import torch.nn.functional as F
import torch
import numpy as np
import warnings
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
from transformers import AutoImageProcessor, ViTModel
from transformers import RobertaTokenizer, RobertaModel
import matplotlib.pyplot as plt

warnings.simplefilter("ignore", category=UserWarning)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
image_processor = AutoImageProcessor.from_pretrained('google/vit-base-patch16-384')

def train(model, dataloader, optimizer, device, criterion):
    model.train()
    total_loss = 0
    total_correct = 0
    total_samples = 0
    all_preds = []
    all_labels = []

    for batch in tqdm(dataloader, desc="Training"):
        input_ids = batch['text']['input_ids'].to(device).squeeze(1)
        attention_mask = batch['text']['attention_mask'].to(device).squeeze(1)
        images = batch['image'].to(device)
        labels = batch['voted_label'].to(device)

        optimizer.zero_grad()
        logits = model(input_ids, attention_mask, images)  # image first
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        preds = torch.argmax(logits, dim=1)
        total_correct += (preds == labels).sum().item()
        total_samples += labels.size(0)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = total_correct / total_samples
    _, _, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='weighted')
    return avg_loss, accuracy, f1

def evaluate(model, dataloader, device, criterion):
    model.eval()
    total_loss = 0
    total_correct = 0
    total_samples = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch['text']['input_ids'].to(device).squeeze(1)
            attention_mask = batch['text']['attention_mask'].to(device).squeeze(1)
            images = batch['image'].to(device)
            labels = batch['voted_label'].to(device)

            logits = model(input_ids, attention_mask, images)
            loss = criterion(logits, labels)

            total_loss += loss.item()
            preds = torch.argmax(logits, dim=1)
            total_correct += (preds == labels).sum().item()
            total_samples += labels.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = total_correct / total_samples
    _, _, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='weighted')

    print(classification_report(all_labels, all_preds, target_names=label_encoder.classes_, digits=4))
    return all_labels, all_preds, avg_loss, accuracy, f1

def tokenize_data(text):
        return tokenizer(text, padding='max_length', truncation=True, max_length=144, return_tensors='pt')

class MultimodalDataset(Dataset):
    def __init__(self, text_encodings, image_paths, labels, image_processor):
        self.text_encodings = text_encodings
        self.image_paths = image_paths
        self.labels = labels
        self.image_processor = image_processor

    def __getitem__(self, idx):
        item = {}
        item['text'] = {key: val[idx] for key, val in self.text_encodings.items()}
        image = Image.open(self.image_paths[idx]).convert("RGB")
        image = self.image_processor(image, return_tensors="pt")['pixel_values'].squeeze(0)
        item['image'] = image
        item['voted_label'] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.labels)

class Model(nn.Module):
    def __init__(self, num_classes=13, embed_dim=512):
        super().__init__()
        self.image_encoder = ViTModel.from_pretrained("google/vit-base-patch16-384")
        self.text_encoder = RobertaModel.from_pretrained("roberta-base")
        # Project image and text features to same dimension
        self.image_proj = nn.Linear(768, embed_dim)
        self.text_proj = nn.Linear(768, embed_dim)
        # Transformer encoder to fuse both modalities
        self.transformer_fusion = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=embed_dim, nhead=8, dim_feedforward=2048, dropout=0.2), 
            num_layers=2)
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, input_ids, attention_mask, image):
        # Encode image and text
        image_feat = self.image_encoder(image).last_hidden_state[:, 0]
        text_feat = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0]
        # Project to same dimensional space
        image_embeds = self.image_proj(image_feat)
        text_embeds = self.text_proj(text_feat)
        # Prepare for Transformer
        fused_input = torch.stack([image_embeds, text_embeds], dim=0)
        # Fuse with Transformer
        fused_output = self.transformer_fusion(fused_input)
        # Average fused output across image/text tokens
        fused_embeds = fused_output.mean(dim=0) #fused_output
        # Classification
        logits = self.classifier(fused_embeds)
        return logits

for RANDOM_STATE in [8, 12, 14]:
    print(f'Starting split: {RANDOM_STATE} ...')
    # load dataset
    dataset1_path = 'labeled_dataset_4688/bc_ab_wildfires.json'
    dataset1 = pd.read_json(dataset1_path)
    # drop uneeded columns
    columns_to_drop1 = ['tweet_id', 'img_id', 'username', 'author_location', 'country_code', 'country', 'full_name', 'posted_at', 'contains_personal_info']
    dataset1 = dataset1.drop(columns=columns_to_drop1)
    # fix image paths
    dataset1['image'] = dataset1['image'].apply(lambda x: x.split('\\')[7])
    base_path1 = 'labeled_dataset_4688/bc_ab_images/'
    dataset1['image'] = dataset1['image'].apply(lambda x: base_path1 + x)
    # load dataset
    dataset2_path = 'labeled_dataset_4688/bc_ab_jasper_07-18_07-25_labeled.csv'
    dataset2 = pd.read_csv(dataset2_path)
    # drop uneeded columns
    columns_to_drop2 = ['tweet_id', 'img_id', 'posted_at', 'author_id', 'author_loc', 'author_name', 'author_usrname', 'media_keys', 'urls', 'predicted_label', 'contains_personal_info']
    dataset2 = dataset2.drop(columns=columns_to_drop2)
    # fix image paths
    dataset2['image'] = dataset2['image'].apply(lambda x: x.split('\\')[7])
    base_path2 = 'labeled_dataset_4688/new_images/'
    dataset2['image'] = dataset2['image'].apply(lambda x: base_path2 + x)

    # combine datasets
    combined_df = pd.concat([dataset1, dataset2]).reset_index(drop=True)

    # add voted labels
    vl_labels_path = 'dataset.csv'
    vl_dataset = pd.read_csv(vl_labels_path)
    combined_df['voted_label'] = vl_dataset['voted_label']

    # shuffle data
    combined_df = combined_df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    # Split the data into train and test sets (80/20 split), stratifying by 'label'
    train_df, test_df = train_test_split(combined_df, test_size=0.2, random_state=RANDOM_STATE, stratify=combined_df['label'])
    test_df = test_df.reset_index(drop=True)
    train_df = train_df.reset_index(drop=True)

    train_text_tokenized = tokenize_data(train_df['text'].tolist())
    test_text_tokenized = tokenize_data(test_df['text'].tolist())

    label_encoder = LabelEncoder()
    train_labels = label_encoder.fit_transform(train_df['voted_label'].values)
    test_labels = label_encoder.transform(test_df['voted_label'].values)

    train_dataset = MultimodalDataset(train_text_tokenized, train_df['image'].tolist(), train_labels, image_processor)
    test_dataset = MultimodalDataset(test_text_tokenized, test_df['image'].tolist(), test_labels, image_processor)
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)
    print('Loaded dataset...')

    model = Model()
    model.to(DEVICE)
    optimizer = AdamW(model.parameters(), lr=1e-5, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss()
    print('Initialized model...')

    model_save_path = f'3foldcv/mmtf_r{RANDOM_STATE}'
    save_path = os.path.join(model_save_path, "checkpoint.pth")
    if not os.path.exists(model_save_path):
        os.makedirs(model_save_path)
    best_f1 = 0
    train_losses = []
    train_accs = []
    test_losses = []
    test_accs = []

    print('Starting training...')
    num_epochs = 10
    for epoch in range(num_epochs):
        train_loss, train_accuracy, train_f1 = train(model, train_loader, optimizer, DEVICE, criterion)
        _, _, test_loss, test_accuracy, test_f1 = evaluate(model, test_loader, DEVICE, criterion)

        print(f'Epoch {epoch + 1}/{num_epochs}')
        print(f'Train F1:   {train_f1:.4f}')
        print(f'Train Acc:  {train_accuracy:.4f}')
        print(f'Train Loss: {train_loss:.4f}')
        print(f'Test F1:    {test_f1:.4f}')
        print(f'Test Acc:   {test_accuracy:.4f}')
        print(f'Test Loss:  {test_loss:.4f}')

        train_losses.append(train_loss)
        train_accs.append(train_accuracy)
        test_losses.append(test_loss)
        test_accs.append(test_accuracy)

        if test_f1 > best_f1:
            best_f1 = test_f1
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': test_loss,
                'f1': test_f1,
                'accuracy': test_accuracy,
            }, save_path)
            print(f"Best model saved with F1: {best_f1:.4f}")
    print('Finished training...')