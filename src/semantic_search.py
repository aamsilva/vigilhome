"""Semantic Search Module - Vector-based search for surveillance events"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SceneEvent:
    """Represents a scene event with description and metadata"""
    event_id: str
    timestamp: datetime
    camera: str
    image_path: Path
    description: str
    detections: List[Dict[str, Any]]
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "camera": self.camera,
            "image_path": str(self.image_path),
            "description": self.description,
            "detections": self.detections,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SceneEvent":
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            camera=data["camera"],
            image_path=Path(data["image_path"]),
            description=data["description"],
            detections=data.get("detections", []),
            confidence=data.get("confidence", 0.0)
        )


class SemanticSearch:
    """
    Semantic search for surveillance events using vector embeddings.
    
    Features:
    - Store scene descriptions with vector embeddings
    - Natural language search over events
    - Temporal and camera filtering
    """
    
    def __init__(self, 
                 persist_directory: Path,
                 collection_name: str = "vigilhome_events",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize semantic search.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
            embedding_model: HuggingFace embedding model name
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = None
        self.collection = None
        self.embedding_model = None
        
        self._init_chromadb()
        
        logger.info(f"SemanticSearch initialized with model {embedding_model}")
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and collection"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use basic settings to avoid Python 3.14 compatibility issues
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "VigilHome surveillance events"}
            )
            
            logger.info(f"ChromaDB collection '{self.collection_name}' ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def _init_embeddings(self):
        """Lazy initialization of embedding model"""
        if self.embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        self._init_embeddings()
        
        if self.embedding_model is None:
            raise RuntimeError("Embedding model not available")
        
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _generate_event_id(self, timestamp: datetime, camera: str, 
                          image_path: Path) -> str:
        """Generate unique event ID"""
        content = f"{timestamp.isoformat()}_{camera}_{image_path}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def index_event(self, 
                   timestamp: datetime,
                   camera: str,
                   image_path: Path,
                   description: str,
                   detections: Optional[List[Dict]] = None,
                   confidence: float = 1.0) -> str:
        """
        Index a scene event for semantic search.
        
        Args:
            timestamp: Event timestamp
            camera: Camera identifier
            image_path: Path to captured image
            description: Natural language description
            detections: List of object detections
            confidence: Overall confidence score
        
        Returns:
            Event ID
        """
        if self.collection is None:
            logger.error("ChromaDB not initialized")
            return ""
        
        event_id = self._generate_event_id(timestamp, camera, image_path)
        
        # Create enhanced description for embedding
        enhanced_description = description
        if detections:
            objects = [d.get('class', 'unknown') for d in detections]
            enhanced_description += f" Objects: {', '.join(objects)}."
        enhanced_description += f" Camera: {camera}. Time: {timestamp.strftime('%H:%M')}."
        
        # Generate embedding
        try:
            embedding = self._generate_embedding(enhanced_description)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return ""
        
        # Prepare metadata
        metadata = {
            "timestamp": timestamp.isoformat(),
            "camera": camera,
            "image_path": str(image_path),
            "description": description,
            "confidence": confidence,
            "date": timestamp.strftime("%Y-%m-%d"),
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday()
        }
        
        # Add to ChromaDB
        try:
            self.collection.add(
                ids=[event_id],
                embeddings=[embedding],
                documents=[enhanced_description],
                metadatas=[metadata]
            )
            logger.debug(f"Indexed event {event_id}")
            return event_id
        except Exception as e:
            logger.error(f"Failed to index event: {e}")
            return ""
    
    def search(self, 
              query: str,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None,
              cameras: Optional[List[str]] = None,
              n_results: int = 10) -> List[Dict]:
        """
        Search events using natural language query.
        
        Args:
            query: Natural language query
            start_time: Filter events after this time
            end_time: Filter events before this time
            cameras: Filter by specific cameras
            n_results: Number of results to return
        
        Returns:
            List of matching events with scores
        """
        if self.collection is None:
            logger.error("ChromaDB not initialized")
            return []
        
        # Generate query embedding
        try:
            query_embedding = self._generate_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []
        
        # Build where clause for filtering
        where_clause = {}
        
        if cameras:
            if len(cameras) == 1:
                where_clause["camera"] = cameras[0]
            else:
                where_clause["$or"] = [{"camera": c} for c in cameras]
        
        # Execute search
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, event_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    document = results['documents'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Convert distance to similarity score (0-1)
                    similarity = 1.0 - (distance / 2.0)
                    
                    # Apply time filtering post-query if needed
                    event_time = datetime.fromisoformat(metadata['timestamp'])
                    
                    if start_time and event_time < start_time:
                        continue
                    if end_time and event_time > end_time:
                        continue
                    
                    formatted_results.append({
                        "event_id": event_id,
                        "timestamp": metadata['timestamp'],
                        "camera": metadata['camera'],
                        "image_path": metadata['image_path'],
                        "description": metadata['description'],
                        "confidence": metadata['confidence'],
                        "similarity": round(similarity, 4),
                        "matched_text": document
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_temporal(self, 
                       query: str,
                       time_expression: str,
                       n_results: int = 10) -> List[Dict]:
        """
        Search with temporal expression parsing.
        
        Args:
            query: Natural language query
            time_expression: Time expression like "yesterday", "last week", "today"
            n_results: Number of results
        
        Returns:
            List of matching events
        """
        start_time, end_time = self._parse_time_expression(time_expression)
        
        return self.search(
            query=query,
            start_time=start_time,
            end_time=end_time,
            n_results=n_results
        )
    
    def _parse_time_expression(self, expression: str) -> tuple:
        """
        Parse natural time expression to datetime range.
        
        Returns:
            (start_time, end_time) tuple
        """
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        expression = expression.lower().strip()
        
        if expression == "today":
            return today, now
        elif expression == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, today
        elif expression == "last week":
            week_ago = today - timedelta(days=7)
            return week_ago, now
        elif expression == "last hour":
            hour_ago = now - timedelta(hours=1)
            return hour_ago, now
        elif expression == "last 24 hours":
            day_ago = now - timedelta(days=1)
            return day_ago, now
        else:
            # Default to last 7 days
            week_ago = today - timedelta(days=7)
            return week_ago, now
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """
        Retrieve a specific event by ID.
        
        Args:
            event_id: Event identifier
        
        Returns:
            Event dict or None
        """
        if self.collection is None:
            return None
        
        try:
            result = self.collection.get(
                ids=[event_id],
                include=["metadatas", "documents"]
            )
            
            if result['ids'] and len(result['ids']) > 0:
                metadata = result['metadatas'][0]
                return {
                    "event_id": event_id,
                    **metadata
                }
        except Exception as e:
            logger.error(f"Failed to get event: {e}")
        
        return None
    
    def get_stats(self) -> Dict:
        """
        Get collection statistics.
        
        Returns:
            Statistics dict
        """
        if self.collection is None:
            return {"error": "ChromaDB not initialized"}
        
        try:
            count = self.collection.count()
            return {
                "total_events": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def delete_old_events(self, days: int = 30) -> int:
        """
        Delete events older than specified days.
        
        Args:
            days: Age threshold in days
        
        Returns:
            Number of deleted events
        """
        if self.collection is None:
            return 0
        
        cutoff = datetime.now() - timedelta(days=days)
        
        try:
            # Query for old events
            results = self.collection.get(
                where={"date": {"$lt": cutoff.strftime("%Y-%m-%d")}}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} old events")
                return len(results['ids'])
            
            return 0
        except Exception as e:
            logger.error(f"Failed to delete old events: {e}")
            return 0


class SimpleTextSearch:
    """
    Fallback text search when ChromaDB is not available.
    Uses simple keyword matching.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.events_file = self.data_dir / "scene_events.jsonl"
        self.events: List[SceneEvent] = []
        self._load_events()
    
    def _load_events(self):
        """Load events from disk"""
        if self.events_file.exists():
            with open(self.events_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.events.append(SceneEvent.from_dict(data))
    
    def index_event(self, timestamp: datetime, camera: str, 
                   image_path: Path, description: str,
                   detections: Optional[List[Dict]] = None,
                   confidence: float = 1.0) -> str:
        """Index event to file"""
        event_id = hashlib.md5(
            f"{timestamp.isoformat()}_{camera}".encode()
        ).hexdigest()[:16]
        
        event = SceneEvent(
            event_id=event_id,
            timestamp=timestamp,
            camera=camera,
            image_path=image_path,
            description=description,
            detections=detections or [],
            confidence=confidence
        )
        
        self.events.append(event)
        
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event.to_dict(), default=str) + '\n')
        
        return event_id
    
    def search(self, query: str, **kwargs) -> List[Dict]:
        """Simple keyword search"""
        query_terms = query.lower().split()
        results = []
        
        for event in reversed(self.events):  # Most recent first
            score = 0
            text = f"{event.description} {event.camera}".lower()
            
            for term in query_terms:
                if term in text:
                    score += 1
            
            if score > 0:
                results.append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "camera": event.camera,
                    "image_path": str(event.image_path),
                    "description": event.description,
                    "similarity": score / len(query_terms),
                    "matched_text": event.description
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:kwargs.get('n_results', 10)]
    
    def get_stats(self) -> Dict:
        return {
            "total_events": len(self.events),
            "mode": "simple_text_fallback"
        }


def create_search_engine(data_dir: Path, use_chroma: bool = True) -> SemanticSearch:
    """
    Factory function to create appropriate search engine.
    
    Args:
        data_dir: Directory for data storage
        use_chroma: Try to use ChromaDB (fallback to text if fails)
    
    Returns:
        SemanticSearch or SimpleTextSearch instance
    """
    if use_chroma:
        try:
            return SemanticSearch(data_dir / "chroma_db")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed, using fallback: {e}")
    
    return SimpleTextSearch(data_dir)


if __name__ == "__main__":
    # Test the semantic search
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        search = create_search_engine(Path(tmpdir))
        
        # Index some test events
        now = datetime.now()
        for i in range(5):
            search.index_event(
                timestamp=now - timedelta(hours=i),
                camera="sala" if i % 2 == 0 else "cozinha",
                image_path=Path(f"/tmp/test_{i}.jpg"),
                description=f"Person walking in the {'living room' if i % 2 == 0 else 'kitchen'}",
                detections=[{"class": "person", "confidence": 0.9}],
                confidence=0.9
            )
        
        # Search
        results = search.search("person in living room", n_results=3)
        print("Search results:")
        for r in results:
            print(f"  - {r['similarity']:.2f}: {r['description']}")
        
        # Stats
        print("\nStats:", search.get_stats())
