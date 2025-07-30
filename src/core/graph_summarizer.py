"""
Graph-based summarization module with progress bars and improved error handling
"""

import networkx as nx
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import string
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import plotly.graph_objs as go
import os
import plotly.io as pio
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

from ..utils.progress import ProgressManager, display_section_header, display_success, display_error, display_info, display_warning
from ..utils.config import Config as AppConfig

class GraphSummarizer:
    """Enhanced graph-based text summarizer with progress tracking"""
    
    def __init__(self):
        """Initialize the GraphSummarizer with NLTK resources"""
        self.stop_words = self._load_stopwords()
    
    def _load_stopwords(self) -> set:
        """Load NLTK stopwords with fallback"""
        try:
            return set(stopwords.words('english'))
        except LookupError:
            import nltk
            nltk.download('stopwords', quiet=True)
            return set(stopwords.words('english'))
    
    def preprocess_sentence(self, sentence: str) -> str:
        """
        Preprocess a sentence by removing stopwords and punctuation
        
        Args:
            sentence: Input sentence
            
        Returns:
            Preprocessed sentence
        """
        # Remove punctuation and tokenize
        table = str.maketrans('', '', string.punctuation)
        tokens = word_tokenize(sentence)
        
        # Clean tokens
        cleaned_tokens = []
        for word in tokens:
            word_lower = word.lower().translate(table)
            if word_lower and word_lower not in self.stop_words:
                cleaned_tokens.append(word_lower)
        
        return ' '.join(cleaned_tokens)
    
    def create_tfidf_matrix(self, corpus: str) -> pd.DataFrame:
        """
        Create TF-IDF matrix from corpus
        
        Args:
            corpus: Input text corpus
            
        Returns:
            DataFrame with TF-IDF features
        """
        try:
            # Tokenize into sentences
            sentences = sent_tokenize(corpus)
        except LookupError:
            import nltk
            nltk.download('punkt', quiet=True)
            sentences = sent_tokenize(corpus)
        
        # Preprocess sentences
        processed_sentences = [self.preprocess_sentence(sent) for sent in sentences]
        
        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(min_df=1, max_df=0.9)
        tfidf_matrix = tfidf.fit_transform(processed_sentences)
        
        # Create DataFrame
        feature_names = tfidf.get_feature_names_out()
        df = pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names)
        
        # Add sentence information
        df['p_sentence'] = [word_tokenize(sent) for sent in processed_sentences]
        df['sentences'] = sentences
        
        return df
    
    def longest_common_subsequence(self, X: str, Y: str) -> int:
        """
        Calculate longest common subsequence length
        
        Args:
            X: First string
            Y: Second string
            
        Returns:
            Length of LCS
        """
        m, n = len(X), len(Y)
        L = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if X[i-1] == Y[j-1]:
                    L[i][j] = L[i-1][j-1] + 1
                else:
                    L[i][j] = max(L[i-1][j], L[i][j-1])
        
        return L[m][n]
    
    def lcs_similarity(self, s1: List[str], s2: List[str]) -> float:
        """
        Calculate LCS-based similarity between word lists
        
        Args:
            s1: First word list
            s2: Second word list
            
        Returns:
            Similarity score
        """
        if not s1:
            return 0.0
        
        s2_copy = s2.copy()
        total_score = 0.0
        
        for w1 in s1:
            if not s2_copy:
                break
            
            max_lcs = 0
            max_idx = -1
            
            for idx, w2 in enumerate(s2_copy):
                lcs_len = self.longest_common_subsequence(w1, w2)
                if lcs_len > max_lcs:
                    max_lcs = lcs_len
                    max_idx = idx
            
            if max_lcs > 0:
                del s2_copy[max_idx]
                if max_lcs / len(w1) >= 0.6:
                    total_score += max_lcs / len(w1)
        
        return total_score / len(s1)
    
    def cosine_similarity(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """
        Calculate cosine similarity between vectors
        
        Args:
            p1: First vector
            p2: Second vector
            
        Returns:
            Cosine similarity score
        """
        dot_product = np.dot(p1, p2)
        magnitude1 = np.sqrt(np.sum(p1 ** 2))
        magnitude2 = np.sqrt(np.sum(p2 ** 2))
        
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def calculate_similarity_matrix(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate similarity matrix between sentences with progress tracking
        
        Args:
            df: DataFrame with TF-IDF features
            
        Returns:
            Tuple of (similarity_matrix, degrees)
        """
        num_rows, num_cols = df.values.shape
        feature_cols = num_cols - 2  # Exclude 'p_sentence' and 'sentences' columns
        
        # Initialize matrices
        similarities = np.zeros((num_rows, num_rows))
        degrees = np.zeros(num_rows)
        
        # Calculate similarities with progress tracking
        total_comparisons = num_rows * (num_rows - 1) // 2
        comparison_count = 0
        
        with ProgressManager("Calculating similarity matrix", total_comparisons) as progress:
            for i in range(num_rows):
                for j in range(num_rows):
                    if i == j:
                        continue
                    
                    # TF-IDF similarity
                    tfidf_sim = self.cosine_similarity(
                        df.iloc[i].values[:feature_cols], 
                        df.iloc[j].values[:feature_cols]
                    )
                    
                    # LCS similarity
                    lcs_sim = self.lcs_similarity(
                        df.iloc[i]['p_sentence'], 
                        df.iloc[j]['p_sentence']
                    )
                    
                    # Combined similarity
                    combined_sim = (AppConfig.GRAPH_SUMMARIZATION_CONFIG['alpha'] * tfidf_sim + 
                                  (1 - AppConfig.GRAPH_SUMMARIZATION_CONFIG['alpha']) * lcs_sim)
                    
                    if combined_sim > AppConfig.GRAPH_SUMMARIZATION_CONFIG['similarity_threshold']:
                        similarities[i][j] = 1.0
                        degrees[j] += 1
                    else:
                        similarities[i][j] = 0.0
                    
                    comparison_count += 1
                    if comparison_count % 100 == 0:
                        progress.update(100, f"Processed {comparison_count}/{total_comparisons} comparisons")
        
        # Normalize by degrees
        for i in range(num_rows):
            if degrees[i] > 0:
                similarities[:, i] /= degrees[i]
        
        return similarities, degrees
    
    def power_method(self, similarity_matrix: np.ndarray, 
                    degrees: np.ndarray) -> np.ndarray:
        """
        Apply power method to find sentence importance scores
        
        Args:
            similarity_matrix: Similarity matrix
            degrees: Degree vector
            
        Returns:
            Importance scores
        """
        n = len(degrees)
        p_initial = np.ones(n) / n
        
        with ProgressManager("Applying power method", AppConfig.GRAPH_SUMMARIZATION_CONFIG['max_loops']) as progress:
            for iteration in range(AppConfig.GRAPH_SUMMARIZATION_CONFIG['max_loops']):
                p_update = np.dot(similarity_matrix.T, p_initial)
                delta = np.linalg.norm(p_update - p_initial)
                
                if delta < AppConfig.GRAPH_SUMMARIZATION_CONFIG['stopping_criterion']:
                    progress.update(AppConfig.GRAPH_SUMMARIZATION_CONFIG['max_loops'] - iteration)
                    break
                
                p_initial = p_update
                progress.update(1)
        
        # Normalize
        p_update /= np.max(p_update)
        return p_update
    
    def _extract_sentences(self, corpus: str) -> List[str]:
        """
        Extract sentences from corpus using NLTK
        
        Args:
            corpus: Input text corpus
            
        Returns:
            List of sentences
        """
        try:
            return sent_tokenize(corpus)
        except LookupError:
            import nltk
            nltk.download('punkt', quiet=True)
            return sent_tokenize(corpus)
    
    def summarize(self, corpus: str, sum_size: int = None) -> str:
        """
        Generate summary using graph-based approach
        
        Args:
            corpus: Input text corpus
            sum_size: Number of sentences in summary
            
        Returns:
            Generated summary
        """
        if sum_size is None:
            sum_size = AppConfig.GRAPH_SUMMARIZATION_CONFIG['default_sum_size']
        
        # Filter out "Article too short to summarize" entries
        sentences = self._extract_sentences(corpus)
        filtered_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (sentence and 
                sentence.lower() != "article too short to summarize." and
                len(sentence.split()) >= 5):  # Minimum 5 words
                filtered_sentences.append(sentence)
        
        if len(filtered_sentences) < 2:
            return "Insufficient content for meaningful summarization."
        
        # Reconstruct corpus with filtered sentences
        corpus = ' '.join(filtered_sentences)
        
        # Check if corpus is too short
        if len(corpus.strip()) < 50:
            return corpus.strip()
        
        # Create TF-IDF matrix
        df = self.create_tfidf_matrix(corpus)
        
        if len(df) == 0:
            return ""
        
        # If we have very few sentences, return the corpus as is
        if len(df) <= 2:
            return corpus.strip()
        
        # Calculate similarity matrix
        similarity_matrix, degrees = self.calculate_similarity_matrix(df)
        
        # Apply power method
        scores = self.power_method(similarity_matrix, degrees)
        
        # Select top sentences, but ensure we don't select too many for short texts
        max_sentences = min(sum_size, len(df))
        top_indices = np.argsort(scores)[::-1][:max_sentences]
        top_indices.sort()  # Maintain original order
        
        # Extract sentences
        selected_sentences = [df.iloc[idx]['sentences'] for idx in top_indices]
        summary = ' '.join(selected_sentences)
        
        # If summary is too short, return the original corpus
        if len(summary.strip()) < 30:
            return corpus.strip()
        
        return summary
    
    def create_graph_visualization(self, similarity_matrix: np.ndarray, 
                                 filename: str, corpus: str = "") -> None:
        """
        Create and save beautiful interactive graph visualization
        
        Args:
            similarity_matrix: Similarity matrix
            filename: Output filename
        """
        try:
            # Create graph
            G = nx.Graph()
            
            # Add edges with weights
            for i in range(len(similarity_matrix)):
                for j in range(i + 1, len(similarity_matrix)):
                    if similarity_matrix[i][j] > 0:
                        G.add_edge(f"Sentence {i+1}", f"Sentence {j+1}", 
                                 weight=similarity_matrix[i][j])
            
            if len(G.edges()) == 0:
                display_warning("No edges found for graph visualization")
                return
            
            # Calculate layout with better spacing
            pos = nx.spring_layout(G, k=3, iterations=50)
            
            # Calculate node sizes based on degree
            node_sizes = [G.degree(node) * 15 + 20 for node in G.nodes()]
            
            # Calculate edge weights for visualization
            edge_weights = [G[u][v]['weight'] * 3 for u, v in G.edges()]
            
            # Create node trace with enhanced styling
            node_trace = go.Scatter(
                x=[], y=[], text=[], mode='markers+text',
                hoverinfo='text', 
                textposition="middle center",
                marker=dict(
                    color=[],
                    size=node_sizes,
                    line=dict(width=2, color='#2E86AB'),
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Node Degree")
                ),
                textfont=dict(size=10, color='white')
            )
            
            # Add nodes with degree-based coloring
            for node in G.nodes():
                x, y = pos[node]
                node_trace['x'] += tuple([x])
                node_trace['y'] += tuple([y])
                node_trace['marker']['color'] += tuple([G.degree(node)])
                node_trace['text'] += tuple([node])
            
            # Create edge trace with enhanced styling
            edge_trace = go.Scatter(
                x=[], y=[], 
                line=dict(width=2, color='#A23B72'), 
                mode='lines',
                hoverinfo='text',
                text=[],
                opacity=0.7
            )
            
            # Add edges with weight information
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_trace['x'] += tuple([x0, x1, None])
                edge_trace['y'] += tuple([y0, y1, None])
                edge_trace['text'] += tuple([f"Similarity: {G[edge[0]][edge[1]]['weight']:.3f}"])
            
            # Create figure with enhanced layout
            fig = go.Figure(data=[edge_trace, node_trace],
                          layout=go.Layout(
                              title=dict(
                                  text='<b>Document Similarity Graph</b><br><sub>Node size indicates degree, edge thickness indicates similarity</sub>',
                                  font=dict(size=20, color='#2E86AB'),
                                  x=0.5
                              ),
                              showlegend=False,
                              hovermode='closest',
                              margin=dict(b=40, l=40, r=40, t=80),
                              xaxis=dict(
                                  showgrid=False, 
                                  zeroline=False, 
                                  showticklabels=False,
                                  range=[-1.2, 1.2]
                              ),
                              yaxis=dict(
                                  showgrid=False, 
                                  zeroline=False, 
                                  showticklabels=False,
                                  range=[-1.2, 1.2]
                              ),
                              plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)',
                              font=dict(family="Arial, sans-serif"),
                              annotations=[
                                  dict(
                                      text="Interactive Graph Visualization",
                                      showarrow=False,
                                      xref="paper", yref="paper",
                                      x=0.5, y=-0.1,
                                      font=dict(size=12, color='#666')
                                  )
                              ]
                          ))
            
            # Add interactive features
            fig.update_layout(
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="right",
                        pad=dict(r=10, t=87),
                        showactive=False,
                        x=0.1,
                        xanchor="left",
                        y=0,
                        yanchor="top",
                        buttons=list([
                            dict(
                                args=[{"visible": [True, True]}],
                                label="Show All",
                                method="update"
                            ),
                            dict(
                                args=[{"visible": [False, True]}],
                                label="Hide Edges",
                                method="update"
                            ),
                            dict(
                                args=[{"visible": [True, False]}],
                                label="Hide Nodes",
                                method="update"
                            )
                        ])
                    )
                ]
            )
            
            # Save figure as PNG
            fig.write_image(filename, width=1200, height=800, scale=2)
            display_success(f"Beautiful graph saved to {filename}")
            
            # Create additional visualizations
            self._create_similarity_heatmap(similarity_matrix, filename)
            self._create_word_cloud_visualization(corpus, filename)
            
        except Exception as e:
            display_error(f"Error creating graph visualization: {str(e)}")
    
    def _create_similarity_heatmap(self, similarity_matrix: np.ndarray, filename: str) -> None:
        """Create similarity heatmap visualization"""
        try:
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=similarity_matrix,
                colorscale='Viridis',
                text=[[f"{val:.3f}" for val in row] for row in similarity_matrix],
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title=dict(
                    text='<b>Sentence Similarity Heatmap</b>',
                    font=dict(size=18, color='#2E86AB'),
                    x=0.5
                ),
                xaxis_title="Sentence Index",
                yaxis_title="Sentence Index",
                width=600,
                height=500,
                plot_bgcolor='white'
            )
            
            heatmap_filename = filename.replace('.png', '_heatmap.png')
            fig.write_image(heatmap_filename, width=800, height=600, scale=2)
            display_success(f"Similarity heatmap saved to {heatmap_filename}")
            
        except Exception as e:
            display_error(f"Error creating heatmap: {str(e)}")
    
    def _create_word_cloud_visualization(self, corpus: str, filename: str) -> None:
        """Create word cloud visualization"""
        try:
            # Tokenize and count words
            words = word_tokenize(corpus.lower())
            word_freq = {}
            
            for word in words:
                if word.isalpha() and word not in self.stop_words and len(word) > 2:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            if not word_freq:
                return
            
            # Get top words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
            
            # Create bubble chart (word cloud alternative)
            words_list, freqs = zip(*top_words)
            
            fig = go.Figure(data=[go.Scatter(
                x=[i for i in range(len(words_list))],
                y=freqs,
                mode='markers+text',
                text=words_list,
                textposition="middle center",
                marker=dict(
                    size=[freq * 2 for freq in freqs],
                    color=freqs,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Word Frequency")
                ),
                textfont=dict(size=10, color='white')
            )])
            
            fig.update_layout(
                title=dict(
                    text='<b>Word Frequency Distribution</b>',
                    font=dict(size=18, color='#2E86AB'),
                    x=0.5
                ),
                xaxis_title="Word Rank",
                yaxis_title="Frequency",
                width=800,
                height=500,
                plot_bgcolor='white'
            )
            
            wordcloud_filename = filename.replace('.png', '_wordcloud.png')
            fig.write_image(wordcloud_filename, width=1000, height=600, scale=2)
            display_success(f"Word frequency visualization saved to {wordcloud_filename}")
            
        except Exception as e:
            display_error(f"Error creating word cloud: {str(e)}")

class FileProcessor:
    """Enhanced file processor with progress tracking"""
    
    def __init__(self, input_dir: Path, output_dir: Path, graphs_dir: Path):
        """
        Initialize the FileProcessor
        
        Args:
            input_dir: Directory with input text files
            output_dir: Directory for summary outputs
            graphs_dir: Directory for graph visualizations
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.graphs_dir = graphs_dir
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_text_files(self) -> List[Path]:
        """Get list of text files to process"""
        return list(self.input_dir.glob('*.txt'))
    
    def process_file(self, text_file: Path, summarizer: GraphSummarizer) -> None:
        """
        Process a single text file
        
        Args:
            text_file: Path to text file
            summarizer: GraphSummarizer instance
        """
        try:
            # Read text
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                display_warning(f"Empty file: {text_file.name}")
                return
            
            # Generate summary
            summary = summarizer.summarize(text, sum_size=1)
            
            # Save summary
            output_file = self.output_dir / f"{text_file.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            # Create graph visualization
            df = summarizer.create_tfidf_matrix(text)
            if len(df) > 1:
                similarity_matrix, _ = summarizer.calculate_similarity_matrix(df)
                graph_file = self.graphs_dir / f"{text_file.stem}.png"
                summarizer.create_graph_visualization(similarity_matrix, str(graph_file), text)
            
            display_success(f"Processed {text_file.name}")
            
        except Exception as e:
            display_error(f"Error processing {text_file.name}: {str(e)}")

def main() -> None:
    """Main execution function with enhanced progress tracking"""
    display_section_header("Graph Summarizer", "Generating graph-based summaries")
    
    # Setup paths
    input_dir = AppConfig.MULTI_SUMMARIES_DIR
    output_dir = AppConfig.FINAL_DIR
    graphs_dir = AppConfig.GRAPHS_DIR
    
    # Validate input directory
    if not input_dir.exists():
        display_error(f"Input directory {input_dir} does not exist.")
        display_warning("Please run summarizer.py first.")
        return
    
    # Initialize components
    summarizer = GraphSummarizer()
    processor = FileProcessor(input_dir, output_dir, graphs_dir)
    
    # Get text files
    text_files = processor.get_text_files()
    if not text_files:
        display_warning(f"No text files found in {input_dir}")
        return
    
    display_info(f"Processing {len(text_files)} files...")
    
    # Process files with progress tracking
    with ProgressManager("Processing files", len(text_files)) as progress:
        for i, text_file in enumerate(text_files):
            processor.process_file(text_file, summarizer)
            progress.update(1, f"Processed {i+1}/{len(text_files)} files")
    
    display_success("Graph summarization completed!")
    display_info(f"Files processed: {len(text_files)}")
    display_success(f"Check {output_dir} for summaries and {graphs_dir} for visualizations")

if __name__ == "__main__":
    main() 