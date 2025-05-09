#!/usr/bin/env python
"""
Open Notebook CLI - Command-line interface for Open Notebook

This script provides an easy-to-use command-line interface for interacting with Open Notebook.
It can be used to manage notebooks, sources, notes, transformations, and more.

Usage:
    python open_notebook_cli.py [command] [options]

Run `python open_notebook_cli.py --help` for more information.
"""

import argparse
import asyncio
import json
import logging # Added
from typing import List, Dict, Any, Optional # Added for type hints

from open_notebook.database.repository import Notebook, Source, Note, Transformation, SourceInsight, ChatSession, PodcastTemplate, PodcastEpisode
from open_notebook.graphs.source import source_graph
from open_notebook.graphs.transformation import transform_graph
from open_notebook.config import config

class OpenNotebookCLI:
    """Command-line interface for Open Notebook"""

    def __init__(self):
        self.parser = self._create_parser()
        self.standard_transformation_ids = [
            "transformation:six06lwh4za956v8b53y",
            "transformation:75oaeqdl73m3vk31sc66",
            "transformation:q2g9i1ijrr37a9ubopku",
            "transformation:5tvf3lsffw5onsh4eecr",
            "transformation:peilrk93qprsggk4pck4",
            "transformation:9d74z8nhwml1c9zi04ng"
        ]
        # Configure logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all commands and options"""
        
        # Main parser
        parser = argparse.ArgumentParser(
            description='Open Notebook CLI - Command-line interface for Open Notebook',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python open_notebook_cli.py list-notebooks
  python open_notebook_cli.py create-notebook "My Research" "Notes about my research project"
  python open_notebook_cli.py list-sources notebook:abc123
  python open_notebook_cli.py add-text-source notebook:abc123 "My Source" "This is the content of my source"
  python open_notebook_cli.py create-note notebook:abc123 "My Note" "This is the content of my note" --type human
  python open_notebook_cli.py search "machine learning" --results 5
"""
        )

        # Create subparsers for different commands
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')

        # === NOTEBOOK COMMANDS ===
        
        # List notebooks
        list_notebooks_parser = subparsers.add_parser('list-notebooks', help='List all notebooks')
        list_notebooks_parser.add_argument('--order-by', default='updated desc', help='Order by field (created, updated)')
        list_notebooks_parser.add_argument('--include-archived', action='store_true', help='Include archived notebooks')
        
        # Get notebook
        get_notebook_parser = subparsers.add_parser('get-notebook', help='Get a specific notebook')
        get_notebook_parser.add_argument('notebook_id', help='ID of the notebook')
        
        # Create notebook
        create_notebook_parser = subparsers.add_parser('create-notebook', help='Create a new notebook')
        create_notebook_parser.add_argument('name', help='Name of the notebook')
        create_notebook_parser.add_argument('description', help='Description of the notebook')
        
        # Archive notebook
        archive_notebook_parser = subparsers.add_parser('archive-notebook', help='Archive a notebook')
        archive_notebook_parser.add_argument('notebook_id', help='ID of the notebook to archive')
        
        # Unarchive notebook
        unarchive_notebook_parser = subparsers.add_parser('unarchive-notebook', help='Unarchive a notebook')
        unarchive_notebook_parser.add_argument('notebook_id', help='ID of the notebook to unarchive')

        # === SOURCE COMMANDS ===
        
        # List sources
        list_sources_parser = subparsers.add_parser('list-sources', help='List all sources in a notebook')
        list_sources_parser.add_argument('notebook_id', help='ID of the notebook')
        
        # Get source
        get_source_parser = subparsers.add_parser('get-source', help='Get a specific source')
        get_source_parser.add_argument('source_id', help='ID of the source')
        get_source_parser.add_argument('--full-text', action='store_true', help='Show the full text of the source')
        get_source_parser.add_argument('--show-insights', action='store_true', help='Show insights for the source')
        
        # Add text source
        add_text_source_parser = subparsers.add_parser('add-text-source', help='Add a text source to a notebook')
        add_text_source_parser.add_argument('notebook_id', help='ID of the notebook')
        add_text_source_parser.add_argument('title', help='Title of the source')
        add_text_source_parser.add_argument('content', help='Content of the source')
        add_text_source_parser.add_argument('--embed', action='store_true', help='Generate embeddings for the source')
        add_text_source_parser.add_argument('--apply-transformations', nargs='*', help='Apply transformations to the source')
        add_text_source_parser.add_argument('--transform', action='store_true', help='Apply a standard set of transformations and automatically enable embedding')
        
        # Add URL source
        add_url_source_parser = subparsers.add_parser('add-url-source', help='Add a URL source to a notebook')
        add_url_source_parser.add_argument('notebook_id', help='ID of the notebook')
        add_url_source_parser.add_argument('url', help='URL of the source')
        add_url_source_parser.add_argument('--embed', action='store_true', help='Generate embeddings for the source')
        add_url_source_parser.add_argument('--apply-transformations', nargs='*', help='Apply transformations to the source')
        add_url_source_parser.add_argument('--transform', action='store_true', help='Apply a standard set of transformations and automatically enable embedding')
        
        # Generate embeddings
        embed_source_parser = subparsers.add_parser('embed-source', help='Generate embeddings for a source')
        embed_source_parser.add_argument('source_id', help='ID of the source')
        
        # === NOTE COMMANDS ===
        
        # List notes
        list_notes_parser = subparsers.add_parser('list-notes', help='List all notes in a notebook')
        list_notes_parser.add_argument('notebook_id', help='ID of the notebook')
        
        # Get note
        get_note_parser = subparsers.add_parser('get-note', help='Get a specific note')
        get_note_parser.add_argument('note_id', help='ID of the note')
        
        # Create note
        create_note_parser = subparsers.add_parser('create-note', help='Create a new note and add it to a notebook')
        create_note_parser.add_argument('notebook_id', help='ID of the notebook')
        create_note_parser.add_argument('title', help='Title of the note')
        create_note_parser.add_argument('content', help='Content of the note')
        create_note_parser.add_argument('--type', choices=['human', 'ai'], default='human', help='Type of note')
        
        # Convert insight to note
        insight_to_note_parser = subparsers.add_parser('insight-to-note', help='Convert a source insight to a note')
        insight_to_note_parser.add_argument('insight_id', help='ID of the source insight')
        insight_to_note_parser.add_argument('notebook_id', help='ID of the notebook')
        
        # === TRANSFORMATION COMMANDS ===
        
        # List transformations
        list_transformations_parser = subparsers.add_parser('list-transformations', help='List all transformations')
        list_transformations_parser.add_argument('--order-by', default='name asc', help='Order by field')
        
        # Get transformation
        get_transformation_parser = subparsers.add_parser('get-transformation', help='Get a specific transformation')
        get_transformation_parser.add_argument('transformation_id', help='ID of the transformation')
        
        # Create transformation
        create_transformation_parser = subparsers.add_parser('create-transformation', help='Create a new transformation')
        create_transformation_parser.add_argument('name', help='Name of the transformation')
        create_transformation_parser.add_argument('title', help='Title for insights generated by this transformation')
        create_transformation_parser.add_argument('description', help='Description of the transformation')
        create_transformation_parser.add_argument('prompt', help='Prompt for the transformation')
        create_transformation_parser.add_argument('--apply-default', action='store_true', help='Apply by default to new sources')
        
        # Apply transformation
        apply_transformation_parser = subparsers.add_parser('apply-transformation', help='Apply a transformation to a source')
        apply_transformation_parser.add_argument('source_id', help='ID of the source')
        apply_transformation_parser.add_argument('transformation_id', nargs='?', help='ID of the transformation')
        apply_transformation_parser.add_argument('--transform', action='store_true', 
                                               help='Apply all standard transformations and automatically enable embedding')
        
        # === CHAT SESSION COMMANDS ===
        
        # List chat sessions
        list_chat_sessions_parser = subparsers.add_parser('list-chat-sessions', help='List all chat sessions for a notebook')
        list_chat_sessions_parser.add_argument('notebook_id', help='ID of the notebook')
        
        # Create chat session
        create_chat_session_parser = subparsers.add_parser('create-chat-session', help='Create a new chat session for a notebook')
        create_chat_session_parser.add_argument('notebook_id', help='ID of the notebook')
        create_chat_session_parser.add_argument('title', help='Title of the chat session')
        
        # === SEARCH COMMANDS ===
        
        # Text search
        text_search_parser = subparsers.add_parser('text-search', help='Perform a text search across sources and notes')
        text_search_parser.add_argument('query', help='Search query')
        text_search_parser.add_argument('--results', type=int, default=10, help='Number of results to return')
        text_search_parser.add_argument('--source', action='store_true', default=True, help='Include sources in search results')
        text_search_parser.add_argument('--note', action='store_true', default=True, help='Include notes in search results')
        
        # Vector search
        vector_search_parser = subparsers.add_parser('vector-search', help='Perform a vector (semantic) search')
        vector_search_parser.add_argument('query', help='Search query')
        vector_search_parser.add_argument('--results', type=int, default=5, help='Number of results to return')
        vector_search_parser.add_argument('--source', action='store_true', default=True, help='Include sources in search results')
        vector_search_parser.add_argument('--note', action='store_true', default=True, help='Include notes in search results')
        vector_search_parser.add_argument('--min-score', type=float, default=0.2, help='Minimum similarity score (0-1)')
        
        # === PODCAST COMMANDS ===
        
        # List podcast templates
        list_podcast_templates_parser = subparsers.add_parser('list-podcast-templates', help='List all podcast templates')
        
        # Get podcast template
        get_podcast_template_parser = subparsers.add_parser('get-podcast-template', help='Get a specific podcast template')
        get_podcast_template_parser.add_argument('template_id', help='ID of the podcast template')
        
        # List podcast episodes
        list_podcast_episodes_parser = subparsers.add_parser('list-podcast-episodes', help='List all podcast episodes')
        list_podcast_episodes_parser.add_argument('--order-by', default='created desc', help='Order by field')
        
        # Generate podcast
        generate_podcast_parser = subparsers.add_parser('generate-podcast', help='Generate a podcast from a notebook')
        generate_podcast_parser.add_argument('template_id', help='ID of the podcast template')
        generate_podcast_parser.add_argument('notebook_id', help='ID of the notebook to generate podcast from')
        generate_podcast_parser.add_argument('episode_name', help='Name of the podcast episode')
        generate_podcast_parser.add_argument('--instructions', help='Additional instructions for podcast generation')
        generate_podcast_parser.add_argument('--longform', action='store_true', help='Generate a longer podcast')
        
        # Export command for JSON output
        parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        return parser

    def run(self):
        """Parse arguments and execute the command"""
        args = self.parser.parse_args()
        
        self.logger.info(f"CLI command '{args.command}' invoked with arguments: {vars(args)}")

        if not args.command:
            self.parser.print_help()
            return
        
        # Execute the requested command
        method_name = args.command.replace('-', '_')
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            try:
                result = method(args)
            except Exception as e:
                self.logger.error(f"Error executing command {args.command}: {e}", exc_info=True)
                if args.json:
                    print(json.dumps({"error": str(e), "command": args.command}, indent=2))
                else:
                    print(f"Error: {e}")
                return

            # Output the result as JSON if requested
            if args.json and result is not None:
                print(json.dumps(result, default=str, indent=2))
        else:
            print(f"Unknown command: {args.command}")
            self.parser.print_help()

    # === NOTEBOOK COMMANDS ===
    
    def _list_notebooks_logic(self, order_by: str, include_archived: bool) -> List[Dict[str, Any]]:
        """Logic for listing notebooks."""
        self.logger.info(f"Fetching notebooks with order_by='{order_by}', include_archived={include_archived}")
        notebooks = Notebook.get_all(order_by=order_by)
        
        if not include_archived:
            notebooks = [nb for nb in notebooks if not nb.archived]
        
        result = []
        for nb in notebooks:
            result.append({
                'id': nb.id,
                'name': nb.name,
                'description': nb.description,
                'created': nb.created,
                'updated': nb.updated,
                'archived': nb.archived
            })
        self.logger.info(f"Found {len(result)} notebooks.")
        return result

    def list_notebooks(self, args):
        """List all notebooks"""
        result = self._list_notebooks_logic(order_by=args.order_by, include_archived=args.include_archived)
            
        if not args.json:
            if not result:
                print("No notebooks found.")
                return result
            for nb_data in result:
                print(f"{nb_data['id']}: {nb_data['name']}")
                print(f"  Description: {nb_data['description']}")
                print(f"  Created: {nb_data['created']}, Updated: {nb_data['updated']}")
                if nb_data['archived']:
                    print("  [ARCHIVED]")
                print()
        
        return result
    
    def get_notebook(self, args):
        """Get a specific notebook"""
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        result = {
            'id': notebook.id,
            'name': notebook.name,
            'description': notebook.description,
            'created': notebook.created,
            'updated': notebook.updated,
            'archived': notebook.archived,
            'sources_count': len(notebook.sources),
            'notes_count': len(notebook.notes),
            'chat_sessions_count': len(notebook.chat_sessions)
        }
        
        if not args.json:
            print(f"Notebook: {notebook.name} ({notebook.id})")
            print(f"Description: {notebook.description}")
            print(f"Created: {notebook.created}, Updated: {notebook.updated}")
            print(f"Archived: {notebook.archived}")
            print(f"Sources: {len(notebook.sources)}")
            print(f"Notes: {len(notebook.notes)}")
            print(f"Chat Sessions: {len(notebook.chat_sessions)}")
        
        return result
    
    def _create_notebook_logic(self, name: str, description: str) -> Dict[str, Any]:
        """Logic for creating a new notebook."""
        self.logger.info(f"Creating notebook with name='{name}'")
        notebook = Notebook(name=name, description=description)
        notebook.save()
        
        result = {
            'id': notebook.id,
            'name': notebook.name,
            'description': notebook.description,
            'created': notebook.created
        }
        self.logger.info(f"Created notebook with ID: {notebook.id}")
        return result

    def create_notebook(self, args):
        """Create a new notebook"""
        result = self._create_notebook_logic(name=args.name, description=args.description)
        
        if not args.json:
            print(f"Created notebook: {result['id']}")
            print(f"Name: {result['name']}")
            print(f"Description: {result['description']}")
        
        return result
    
    def archive_notebook(self, args):
        """Archive a notebook"""
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        notebook.archived = True
        notebook.save()
        
        if not args.json:
            print(f"Archived notebook: {notebook.name} ({notebook.id})")
        
        return {'id': notebook.id, 'name': notebook.name, 'archived': True}
    
    def unarchive_notebook(self, args):
        """Unarchive a notebook"""
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        notebook.archived = False
        notebook.save()
        
        if not args.json:
            print(f"Unarchived notebook: {notebook.name} ({notebook.id})")
        
        return {'id': notebook.id, 'name': notebook.name, 'archived': False}

    # === SOURCE COMMANDS ===
    
    def list_sources(self, args):
        """List all sources in a notebook"""
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        sources = notebook.sources
        result = []
        
        for source in sources:
            source_info = {
                'id': source.id,
                'title': source.title,
                'created': source.created,
                'updated': source.updated,
                'embedded_chunks': source.embedded_chunks,
                'insights_count': len(source.insights)
            }
            result.append(source_info)
            
            if not args.json:
                print(f"{source.id}: {source.title or 'No Title'}")
                print(f"  Created: {source.created}, Updated: {source.updated}")
                print(f"  Embedded chunks: {source.embedded_chunks}")
                print(f"  Insights: {len(source.insights)}")
                print()
        
        return result
    
    def get_source(self, args):
        """Get a specific source"""
        source = Source.get(args.source_id)
        if not source:
            print(f"Source not found: {args.source_id}")
            return None
        
        result = {
            'id': source.id,
            'title': source.title,
            'created': source.created,
            'updated': source.updated,
            'embedded_chunks': source.embedded_chunks,
            'insights_count': len(source.insights)
        }
        
        if args.full_text:
            result['full_text'] = source.full_text
        
        if args.show_insights:
            insights = []
            for insight in source.insights:
                insights.append({
                    'id': insight.id,
                    'insight_type': insight.insight_type,
                    'content': insight.content
                })
            result['insights'] = insights
        
        if not args.json:
            print(f"Source: {source.title or 'No Title'} ({source.id})")
            print(f"Created: {source.created}, Updated: {source.updated}")
            print(f"Embedded chunks: {source.embedded_chunks}")
            print(f"Insights: {len(source.insights)}")
            
            if args.full_text:
                print("\nFull Text:")
                print(source.full_text[:1000] + ('...' if len(source.full_text) > 1000 else ''))
            
            if args.show_insights:
                print("\nInsights:")
                for insight in source.insights:
                    print(f"\n{insight.insight_type}:")
                    print(insight.content[:500] + ('...' if len(insight.content) > 500 else ''))
        
        return result
    
    def add_text_source(self, args):
        """Add a text source to a notebook
        
        Supports the --transform parameter to apply standard transformations and automatically enable embedding.
        """
        content_state = {
            'content': args.content,
            'title': args.title
        }
        
        apply_transformations = []
        if args.transform:
            # Use standard transformation IDs
            for t_id in self.standard_transformation_ids:
                transformation = Transformation.get(t_id)
                if transformation:
                    apply_transformations.append(transformation)
        elif args.apply_transformations:
            for t_id in args.apply_transformations:
                transformation = Transformation.get(t_id)
                if transformation:
                    apply_transformations.append(transformation)
        
        result = asyncio.run(source_graph.ainvoke({
            'content_state': content_state,
            'notebook_id': args.notebook_id,
            'apply_transformations': apply_transformations,
            'embed': args.embed or args.transform  # Automatically enable embed if transform is set
        }))
        
        source = result["source"]
        
        if not args.json:
            print(f"Added text source: {source.id}")
            print(f"Title: {source.title}")
            
            if args.embed or args.transform:
                print(f"Embedded chunks: {source.embedded_chunks}")
            
            if args.transform:
                print(f"Applied {len(self.standard_transformation_ids)} standard transformations")
                print("Use 'get-source --show-insights' to view the transformation results")
            elif apply_transformations:
                print(f"Applied {len(apply_transformations)} transformations")
        
        return {
            'id': source.id,
            'title': source.title,
            'embedded_chunks': source.embedded_chunks if (args.embed or args.transform) else 0
        }
    
    def add_url_source(self, args):
        """Add a URL source to a notebook
        
        Supports the --transform parameter to apply standard transformations and automatically enable embedding.
        """
        content_state = {
            'url': args.url
        }
        
        apply_transformations = []
        if args.transform:
            # Use standard transformation IDs
            for t_id in self.standard_transformation_ids:
                transformation = Transformation.get(t_id)
                if transformation:
                    apply_transformations.append(transformation)
        elif args.apply_transformations:
            for t_id in args.apply_transformations:
                transformation = Transformation.get(t_id)
                if transformation:
                    apply_transformations.append(transformation)
        
        result = asyncio.run(source_graph.ainvoke({
            'content_state': content_state,
            'notebook_id': args.notebook_id,
            'apply_transformations': apply_transformations,
            'embed': args.embed or args.transform  # Automatically enable embed if transform is set
        }))
        
        source = result["source"]
        
        if not args.json:
            print(f"Added URL source: {source.id}")
            print(f"Title: {source.title}")
            print(f"URL: {args.url}")
            
            if args.embed or args.transform:
                print(f"Embedded chunks: {source.embedded_chunks}")
            
            if args.transform:
                print(f"Applied {len(self.standard_transformation_ids)} standard transformations")
                print("Use 'get-source --show-insights' to view the transformation results")
            elif apply_transformations:
                print(f"Applied {len(apply_transformations)} transformations")
        
        return {
            'id': source.id,
            'title': source.title,
            'url': args.url,
            'embedded_chunks': source.embedded_chunks if (args.embed or args.transform) else 0
        }
    
    def embed_source(self, args):
        """Generate embeddings for a source"""
        source = Source.get(args.source_id)
        if not source:
            print(f"Source not found: {args.source_id}")
            return None
        
        original_chunks = source.embedded_chunks
        source.vectorize()
        new_chunks = source.embedded_chunks
        
        if not args.json:
            print(f"Generated embeddings for source: {source.title or 'No Title'} ({source.id})")
            print(f"Chunks: {new_chunks}")
            if original_chunks > 0:
                print(f"Added {new_chunks - original_chunks} new chunks")
        
        return {
            'id': source.id,
            'title': source.title,
            'embedded_chunks': new_chunks,
            'new_chunks': new_chunks - original_chunks
        }

    # === NOTE COMMANDS ===
    
    def list_notes(self, args):
        """List all notes in a notebook"""
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        notes = notebook.notes
        result = []
        
        for note in notes:
            note_info = {
                'id': note.id,
                'title': note.title,
                'note_type': note.note_type,
                'created': note.created,
                'updated': note.updated
            }
            result.append(note_info)
            
            if not args.json:
                print(f"{note.id}: {note.title or 'No Title'}")
                print(f"  Type: {note.note_type}")
                print(f"  Created: {note.created}, Updated: {note.updated}")
                print()
        
        return result
    
    def get_note(self, args):
        """Get a specific note"""
        note = Note.get(args.note_id)
        if not note:
            print(f"Note not found: {args.note_id}")
            return None
        
        result = {
            'id': note.id,
            'title': note.title,
            'note_type': note.note_type,
            'created': note.created,
            'updated': note.updated,
            'content': note.content
        }
        
        if not args.json:
            print(f"Note: {note.title or 'No Title'} ({note.id})")
            print(f"Type: {note.note_type}")
            print(f"Created: {note.created}, Updated: {note.updated}")
            print("\nContent:")
            print(note.content)
        
        return result
    
    def create_note(self, args):
        """Create a new note and add it to a notebook"""
        note = Note(
            title=args.title,
            content=args.content,
            note_type=args.type
        )
        note.save()
        note.add_to_notebook(args.notebook_id)
        
        result = {
            'id': note.id,
            'title': note.title,
            'note_type': note.note_type,
            'created': note.created
        }
        
        if not args.json:
            print(f"Created note: {note.id}")
            print(f"Title: {note.title}")
            print(f"Type: {note.note_type}")
        
        return result
    
    def insight_to_note(self, args):
        """Convert a source insight to a note"""
        insight = SourceInsight.get(args.insight_id)
        if not insight:
            print(f"Source insight not found: {args.insight_id}")
            return None
        
        note = insight.save_as_note(args.notebook_id)
        
        result = {
            'id': note.id,
            'title': note.title,
            'note_type': note.note_type,
            'created': note.created,
            'source_insight_id': insight.id
        }
        
        if not args.json:
            print(f"Created note from insight: {note.id}")
            print(f"Title: {note.title}")
            print(f"Source insight: {insight.id} ({insight.insight_type})")
        
        return result

    # === TRANSFORMATION COMMANDS ===
    
    def list_transformations(self, args):
        """List all transformations"""
        transformations = Transformation.get_all(order_by=args.order_by)
        result = []
        
        for t in transformations:
            t_info = {
                'id': t.id,
                'name': t.name,
                'title': t.title,
                'description': t.description,
                'apply_default': t.apply_default
            }
            result.append(t_info)
            
            if not args.json:
                print(f"{t.id}: {t.name}")
                print(f"  Title: {t.title}")
                print(f"  Description: {t.description}")
                print(f"  Apply by default: {t.apply_default}")
                print()
        
        return result
    
    def get_transformation(self, args):
        """Get a specific transformation"""
        transformation = Transformation.get(args.transformation_id)
        if not transformation:
            print(f"Transformation not found: {args.transformation_id}")
            return None
        
        result = {
            'id': transformation.id,
            'name': transformation.name,
            'title': transformation.title,
            'description': transformation.description,
            'prompt': transformation.prompt,
            'apply_default': transformation.apply_default
        }
        
        if not args.json:
            print(f"Transformation: {transformation.name} ({transformation.id})")
            print(f"Title: {transformation.title}")
            print(f"Description: {transformation.description}")
            print(f"Apply by default: {transformation.apply_default}")
            print("\nPrompt:")
            print(transformation.prompt)
        
        return result
    
    def create_transformation(self, args):
        """Create a new transformation"""
        transformation = Transformation(
            name=args.name,
            title=args.title,
            description=args.description,
            prompt=args.prompt,
            apply_default=args.apply_default
        )
        transformation.save()
        
        result = {
            'id': transformation.id,
            'name': transformation.name,
            'title': transformation.title,
            'description': transformation.description,
            'apply_default': transformation.apply_default
        }
        
        if not args.json:
            print(f"Created transformation: {transformation.id}")
            print(f"Name: {transformation.name}")
            print(f"Title: {transformation.title}")
            print(f"Apply by default: {transformation.apply_default}")
        
        return result
    
    def apply_transformation(self, args):
        """Apply a transformation to a source"""
        source = Source.get(args.source_id)
        if not source:
            print(f"Source not found: {args.source_id}")
            return None
        
        if args.transform:
            # Apply multiple standard transformations
            results = []
            if not args.json:
                print(f"Applying {len(self.standard_transformation_ids)} standard transformations to source: {args.source_id}")
                print("This may take a few minutes...")
            
            for t_id in self.standard_transformation_ids:
                transformation = Transformation.get(t_id)
                if not transformation:
                    print(f"Transformation not found: {t_id}")
                    continue
                
                result = asyncio.run(transform_graph.ainvoke(dict(
                    source=source, 
                    transformation=transformation
                )))
                
                output = result.get("output", "")
                results.append({
                    "transformation_id": t_id,
                    "transformation_name": transformation.name,
                    "output": output
                })
                
                if not args.json:
                    print(f"✓ Applied: {transformation.name}")
            
            if not args.json:
                print(f"Completed {len(results)} transformations on source: {args.source_id}")
            
            # Also embed the source if transform flag is set
            if not source.embedded_chunks:
                if not args.json:
                    print("Generating embeddings for source...")
                self.embed_source(args)
            
            return results
        else:
            # Apply a single transformation
            if not args.transformation_id:
                print("Error: transformation_id is required when --transform is not specified")
                return None
                
            transformation = Transformation.get(args.transformation_id)
            if not transformation:
                print(f"Transformation not found: {args.transformation_id}")
                return None
            
            result = asyncio.run(transform_graph.ainvoke(dict(
                source=source, 
                transformation=transformation
            )))
            
            output = result.get("output", "")
            
            if not args.json:
                print(f"Applied transformation: {transformation.name} to source: {args.source_id}")
                print(f"Output length: {len(output)} characters")
                print(f"Generated insight: {transformation.title}")
                print("\nOutput Preview:")
                print(output[:500] + ('...' if len(output) > 500 else ''))
            
            return {
                "transformation_id": args.transformation_id,
                "transformation_name": transformation.name,
                "insight_type": transformation.title,
                "output": output,
                "output_preview": output[:500] + ('...' if len(output) > 500 else '')
            }

    # === CHAT SESSION COMMANDS ===
    
    def list_chat_sessions(self, args):
        """List all chat sessions for a notebook"""
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        sessions = notebook.chat_sessions
        result = []
        
        for session in sessions:
            session_info = {
                'id': session.id,
                'title': session.title,
                'created': session.created,
                'updated': session.updated
            }
            result.append(session_info)
            
            if not args.json:
                print(f"{session.id}: {session.title or 'No Title'}")
                print(f"  Created: {session.created}, Updated: {session.updated}")
                print()
        
        return result
    
    def create_chat_session(self, args):
        """Create a new chat session for a notebook"""
        chat_session = ChatSession(title=args.title)
        chat_session.save()
        chat_session.relate_to_notebook(args.notebook_id)
        
        result = {
            'id': chat_session.id,
            'title': chat_session.title,
            'created': chat_session.created
        }
        
        if not args.json:
            print(f"Created chat session: {chat_session.id}")
            print(f"Title: {chat_session.title}")
        
        return result

    # === SEARCH COMMANDS ===
    
    def text_search(self, args):
        """Perform a text search across sources and notes"""
        results = text_search(
            keyword=args.query,
            results=args.results,
            source=args.source,
            note=args.note
        )
        
        formatted_results = []
        
        for result in results:
            item = {
                'id': result.get('id'),
                'type': result.get('type'),
                'title': result.get('title'),
                'content': result.get('content')
            }
            formatted_results.append(item)
            
            if not args.json:
                print(f"{result.get('type')}: {result.get('title')} ({result.get('id')})")
                content = result.get('content', '')
                print(content[:300] + ('...' if len(content) > 300 else ''))
                print()
        
        return formatted_results
    
    def vector_search(self, args):
        """Perform a vector (semantic) search"""
        results = vector_search(
            keyword=args.query,
            results=args.results,
            source=args.source,
            note=args.note,
            minimum_score=args.min_score
        )
        
        formatted_results = []
        
        for result in results:
            item = {
                'id': result.get('id'),
                'type': result.get('type'),
                'title': result.get('title'),
                'content': result.get('content'),
                'score': result.get('score')
            }
            formatted_results.append(item)
            
            if not args.json:
                print(f"{result.get('type')}: {result.get('title')} ({result.get('id')})")
                print(f"Score: {result.get('score')}")
                content = result.get('content', '')
                print(content[:300] + ('...' if len(content) > 300 else ''))
                print()
        
        return formatted_results

    # === PODCAST COMMANDS ===
    
    def list_podcast_templates(self, args):
        """List all podcast templates"""
        templates = PodcastConfig.get_all()
        result = []
        
        for template in templates:
            template_info = {
                'id': template.id,
                'name': template.name,
                'podcast_name': template.podcast_name,
                'podcast_tagline': template.podcast_tagline,
                'output_language': template.output_language,
                'provider': template.provider,
                'model': template.model
            }
            result.append(template_info)
            
            if not args.json:
                print(f"{template.id}: {template.name}")
                print(f"  Podcast: {template.podcast_name} - {template.podcast_tagline}")
                print(f"  Language: {template.output_language}")
                print(f"  Provider: {template.provider}, Model: {template.model}")
                print()
        
        return result
    
    def get_podcast_template(self, args):
        """Get a specific podcast template"""
        template = PodcastConfig.get(args.template_id)
        if not template:
            print(f"Podcast template not found: {args.template_id}")
            return None
        
        result = {
            'id': template.id,
            'name': template.name,
            'podcast_name': template.podcast_name,
            'podcast_tagline': template.podcast_tagline,
            'output_language': template.output_language,
            'person1_role': template.person1_role,
            'person2_role': template.person2_role,
            'conversation_style': template.conversation_style,
            'engagement_technique': template.engagement_technique,
            'dialogue_structure': template.dialogue_structure,
            'creativity': template.creativity,
            'provider': template.provider,
            'model': template.model,
            'voice1': template.voice1,
            'voice2': template.voice2
        }
        
        if not args.json:
            print(f"Podcast Template: {template.name} ({template.id})")
            print(f"Podcast: {template.podcast_name} - {template.podcast_tagline}")
            print(f"Language: {template.output_language}")
            print(f"Person 1 Roles: {', '.join(template.person1_role)}")
            print(f"Person 2 Roles: {', '.join(template.person2_role)}")
            print(f"Conversation Style: {', '.join(template.conversation_style)}")
            print(f"Engagement Techniques: {', '.join(template.engagement_technique)}")
            print(f"Dialogue Structure: {', '.join(template.dialogue_structure)}")
            print(f"Creativity: {template.creativity}")
            print(f"Provider: {template.provider}")
            print(f"Model: {template.model}")
            print(f"Voices: {template.voice1}, {template.voice2}")
        
        return result
    
    def list_podcast_episodes(self, args):
        """List all podcast episodes"""
        episodes = PodcastEpisode.get_all(order_by=args.order_by)
        result = []
        
        for episode in episodes:
            episode_info = {
                'id': episode.id,
                'name': episode.name,
                'template': episode.template,
                'created': episode.created,
                'audio_file': episode.audio_file
            }
            result.append(episode_info)
            
            if not args.json:
                print(f"{episode.id}: {episode.name}")
                print(f"  Template: {episode.template}")
                print(f"  Created: {episode.created}")
                print(f"  Audio file: {episode.audio_file}")
                print()
        
        return result
    
    def generate_podcast(self, args):
        """Generate a podcast from a notebook"""
        template = PodcastConfig.get(args.template_id)
        if not template:
            print(f"Podcast template not found: {args.template_id}")
            return None
        
        notebook = Notebook.get(args.notebook_id)
        if not notebook:
            print(f"Notebook not found: {args.notebook_id}")
            return None
        
        # Gather content from notebook sources and notes
        sources = notebook.sources
        notes = notebook.notes
        content = []
        
        for source in sources:
            if source.full_text:
                content.append(source.full_text)
        
        for note in notes:
            if note.content:
                content.append(note.content)
        
        combined_content = "\n\n".join(content)
        
        # Generate podcast
        if not args.json:
            print("Generating podcast, this may take a while...")
        
        template.generate_episode(
            episode_name=args.episode_name,
            text=combined_content,
            instructions=args.instructions or "",
            longform=args.longform
        )
        
        if not args.json:
            print(f"Generated podcast episode: {args.episode_name}")
            print(f"Using template: {template.name}")
            print("Check the podcast episodes list to access the audio file.")
        
        return {
            'episode_name': args.episode_name,
            'template_id': template.id,
            'template_name': template.name,
            'notebook_id': notebook.id,
            'notebook_name': notebook.name,
            'status': 'generated'
        }


if __name__ == "__main__":
    cli = OpenNotebookCLI()
    cli.run()