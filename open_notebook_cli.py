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
import json
import sys
import logging

# Assuming your models are in open_notebook.domain.models
try:
    from open_notebook.domain.models import (
        Notebook, Source, Note, Transformation, ChatSession, 
        PodcastTemplate, PodcastEpisode, SourceInsight
    )
except ImportError as e:
    print(f"Error importing Open Notebook modules: {e}. Ensure PYTHONPATH is set correctly or the package is installed.", file=sys.stderr)

# Custom Exceptions for CLI
class CLIBaseException(Exception):
    """Base class for CLI related exceptions."""
    pass

class CLINotFoundException(CLIBaseException):
    """Raised when a resource (e.g., notebook, source) is not found."""
    pass

class CLIInvalidInputException(CLIBaseException):
    """Raised for invalid user input to a CLI command."""
    pass

class CLIExecutionException(CLIBaseException):
    """Raised for general errors during command execution."""
    pass

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenNotebookCLI:
    """Command-line interface for Open Notebook"""

    def __init__(self):
        self.parser = self._create_parser()

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
        list_notebooks_parser.add_argument('--include-archived', action='store_true', help='Include archived notebooks')
        list_notebooks_parser.add_argument('--order-by', default='created desc', help='Order by field (e.g., "name asc", "created desc")')

        # Get notebook
        get_notebook_parser = subparsers.add_parser('get-notebook', help='Get a specific notebook')
        get_notebook_parser.add_argument('notebook_id', help='ID of the notebook')

        # Create notebook
        create_notebook_parser = subparsers.add_parser('create-notebook', help='Create a new notebook')
        create_notebook_parser.add_argument('name', help='Name of the notebook')
        create_notebook_parser.add_argument('description', nargs='?', default='', help='Description of the notebook')

        # Archive notebook
        archive_notebook_parser = subparsers.add_parser('archive-notebook', help='Archive a notebook')
        archive_notebook_parser.add_argument('notebook_id', help='ID of the notebook')

        # Unarchive notebook
        unarchive_notebook_parser = subparsers.add_parser('unarchive-notebook', help='Unarchive a notebook')
        unarchive_notebook_parser.add_argument('notebook_id', help='ID of the notebook')

        # === SOURCE COMMANDS ===
        list_sources_parser = subparsers.add_parser('list-sources', help='List all sources in a notebook')
        list_sources_parser.add_argument('notebook_id', help='ID of the notebook')

        get_source_parser = subparsers.add_parser('get-source', help='Get a specific source')
        get_source_parser.add_argument('source_id', help='ID of the source')
        get_source_parser.add_argument('--full-text', action='store_true', help='Include full text of the source')
        get_source_parser.add_argument('--show-insights', action='store_true', help='Include insights for the source')

        add_text_source_parser = subparsers.add_parser('add-text-source', help='Add a text source to a notebook')
        add_text_source_parser.add_argument('notebook_id', help='ID of the notebook')
        add_text_source_parser.add_argument('title', help='Title of the source')
        add_text_source_parser.add_argument('content', help='Content of the source')
        add_text_source_parser.add_argument('--embed', action='store_true', help='Generate embeddings for the source')
        add_text_source_parser.add_argument('--apply-transformations', nargs='*', help='List of transformation IDs to apply')
        add_text_source_parser.add_argument('--transform', action='store_true', help='Apply standard transformations')
        
        add_url_source_parser = subparsers.add_parser('add-url-source', help='Add a URL source to a notebook')
        add_url_source_parser.add_argument('notebook_id', help='ID of the notebook')
        add_url_source_parser.add_argument('url', help='URL of the source')
        add_url_source_parser.add_argument('--embed', action='store_true', help='Generate embeddings for the source')
        add_url_source_parser.add_argument('--apply-transformations', nargs='*', help='List of transformation IDs to apply')
        add_url_source_parser.add_argument('--transform', action='store_true', help='Apply standard transformations')

        embed_source_parser = subparsers.add_parser('embed-source', help='Generate embeddings for a source')
        embed_source_parser.add_argument('source_id', help='ID of the source')

        # === NOTE COMMANDS ===
        list_notes_parser = subparsers.add_parser('list-notes', help='List notes in a notebook')
        list_notes_parser.add_argument('notebook_id', help='ID of the notebook')

        get_note_parser = subparsers.add_parser('get-note', help='Get details of a note')
        get_note_parser.add_argument('note_id', help='ID of the note')

        create_note_parser = subparsers.add_parser('create-note', help='Create a new note')
        create_note_parser.add_argument('notebook_id', help='ID of the notebook')
        create_note_parser.add_argument('title', help='Title of the note')
        create_note_parser.add_argument('content', help='Content of the note')
        create_note_parser.add_argument('--type', default='human', choices=['human', 'ai'], help='Type of the note (human or ai)')

        insight_to_note_parser = subparsers.add_parser('insight-to-note', help='Convert source insight to note')
        insight_to_note_parser.add_argument('source_insight_id', help='ID of the source insight')
        insight_to_note_parser.add_argument('notebook_id', help='ID of the notebook to add the note to')

        # === TRANSFORMATION COMMANDS ===
        subparsers.add_parser('list-transformations', help='List all transformations')

        get_transformation_parser = subparsers.add_parser('get-transformation', help='Get details of a transformation')
        get_transformation_parser.add_argument('transformation_id', help='ID of the transformation')

        create_transformation_parser = subparsers.add_parser('create-transformation', help='Create a new transformation')
        create_transformation_parser.add_argument('name', help='Name of the transformation')
        create_transformation_parser.add_argument('short_code', help='Short code for the transformation')
        create_transformation_parser.add_argument('description', help='Description of the transformation')
        create_transformation_parser.add_argument('prompt_template', help='Prompt template for the transformation')
        create_transformation_parser.add_argument('--apply-default', action='store_true', help='Apply this transformation by default to new sources')

        apply_transformation_parser = subparsers.add_parser('apply-transformation', help='Apply transformation to source')
        apply_transformation_parser.add_argument('source_id', help='ID of the source')
        apply_transformation_parser.add_argument('transformation_id', nargs='?', help='ID of the transformation to apply (optional if --transform is used)')
        apply_transformation_parser.add_argument('--transform', action='store_true', help='Apply a standard set of transformations')

        # === CHAT COMMANDS ===
        list_chat_sessions_parser = subparsers.add_parser('list-chat-sessions', help='List chat sessions for a notebook')
        list_chat_sessions_parser.add_argument('notebook_id', help='ID of the notebook')

        create_chat_session_parser = subparsers.add_parser('create-chat-session', help='Create a new chat session')
        create_chat_session_parser.add_argument('notebook_id', help='ID of the notebook')
        create_chat_session_parser.add_argument('title', help='Title of the chat session')
        
        # === SEARCH COMMANDS ===
        text_search_parser = subparsers.add_parser('text-search', help='Perform a text search across sources and notes')
        text_search_parser.add_argument('query', help='Search query')
        text_search_parser.add_argument('--results', type=int, default=10, help='Number of results to return')
        text_search_parser.add_argument('--source', action='store_true', default=None, help='Include sources in search results') # Default None to distinguish from explicit false
        text_search_parser.add_argument('--no-source', action='store_false', dest='source', help='Exclude sources from search results')
        text_search_parser.add_argument('--note', action='store_true', default=None, help='Include notes in search results') # Default None
        text_search_parser.add_argument('--no-note', action='store_false', dest='note', help='Exclude notes from search results')
        
        vector_search_parser = subparsers.add_parser('vector-search', help='Perform a vector (semantic) search')
        vector_search_parser.add_argument('query', help='Search query')
        vector_search_parser.add_argument('--results', type=int, default=5, help='Number of results to return')
        vector_search_parser.add_argument('--source', action='store_true', default=None, help='Include sources in search results')
        vector_search_parser.add_argument('--no-source', action='store_false', dest='source', help='Exclude sources from search results')
        vector_search_parser.add_argument('--note', action='store_true', default=None, help='Include notes in search results')
        vector_search_parser.add_argument('--no-note', action='store_false', dest='note', help='Exclude notes from search results')
        vector_search_parser.add_argument('--min-score', type=float, default=0.2, help='Minimum similarity score (0-1)')
        
        # === PODCAST COMMANDS ===
        subparsers.add_parser('list-podcast-templates', help='List all podcast templates')
        
        get_podcast_template_parser = subparsers.add_parser('get-podcast-template', help='Get a specific podcast template')
        get_podcast_template_parser.add_argument('template_id', help='ID of the podcast template')
        
        list_podcast_episodes_parser = subparsers.add_parser('list-podcast-episodes', help='List all podcast episodes')
        list_podcast_episodes_parser.add_argument('--order-by', default='created desc', help='Order by field')
        
        generate_podcast_parser = subparsers.add_parser('generate-podcast', help='Generate a podcast from a notebook')
        generate_podcast_parser.add_argument('template_id', help='ID of the podcast template')
        generate_podcast_parser.add_argument('notebook_id', help='ID of the notebook to generate podcast from')
        generate_podcast_parser.add_argument('episode_name', help='Name of the podcast episode')
        generate_podcast_parser.add_argument('--instructions', help='Additional instructions for podcast generation')
        generate_podcast_parser.add_argument('--longform', action='store_true', help='Generate a longer podcast')

        get_help_parser = subparsers.add_parser('get-command-help', help='Get help text for a specific command')
        get_help_parser.add_argument('subcommand_name', help='The name of the command to get help for')

        return parser

    def run(self):
        """Parse arguments and execute the command"""
        args = self.parser.parse_args()
        
        method_name = args.command.replace('-', '_')
        if hasattr(self, method_name):
            try:
                # Handle default booleans for search commands if not explicitly set
                if args.command in ['text-search', 'vector-search']:
                    if args.source is None and args.note is None:
                        args.source = True
                        args.note = True
                    elif args.source is None:
                        args.source = True # Default to true if other is specified
                    elif args.note is None:
                        args.note = True # Default to true if other is specified

                result = getattr(self, method_name)(args)
                if hasattr(args, 'json') and args.json and result is not None:
                    print(json.dumps(result, indent=4, default=str))
            except CLIBaseException as e:
                logger.error(f"CLI Error ({type(e).__name__}): {e}")
                error_payload = {"error": str(e), "type": type(e).__name__}
                if hasattr(args, 'json') and args.json:
                    print(json.dumps(error_payload, indent=4))
                else:
                    print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                logger.exception(f"An unexpected error occurred while running command {args.command}: {e}")
                error_payload = {"error": str(e), "type": "UnexpectedError"}
                if hasattr(args, 'json') and args.json:
                    print(json.dumps(error_payload, indent=4))
                else:
                    print(f"An unexpected error occurred: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            logger.error(f"Unknown command: {args.command}")
            self.parser.print_help()
            sys.exit(1)

    # === NOTEBOOK COMMANDS ===
    def list_notebooks(self, args):
        logger.info(f"Listing notebooks with args: {args}")
        try:
            # Placeholder: notebooks = Notebook.get_all(order_by=args.order_by)
            notebooks_data = [
                {'id': 'nb_1', 'name': 'Notebook 1', 'description': 'Desc 1', 'created': '2023-01-01T10:00:00', 'updated': '2023-01-01T11:00:00', 'archived': False},
                {'id': 'nb_2', 'name': 'Archived NB', 'description': 'Desc 2', 'created': '2023-01-02T10:00:00', 'updated': '2023-01-02T11:00:00', 'archived': True}
            ]
            # Simulate filtering and ordering if Notebook.get_all was real
            if not args.include_archived:
                notebooks_data = [nb for nb in notebooks_data if not nb['archived']]
            # Simulate ordering (very basic)
            if 'created' in args.order_by:
                notebooks_data.sort(key=lambda x: x['created'], reverse='desc' in args.order_by)
            
        except Exception as e:
            logger.error(f"Failed to retrieve notebooks: {e}")
            raise CLIExecutionException(f"Database error while listing notebooks: {e}")
        
        result = []
        for nb_data in notebooks_data:
            result.append(nb_data)
            if not args.json:
                print(f"ID: {nb_data['id']}, Name: {nb_data['name']}, Archived: {nb_data['archived']}, Created: {nb_data['created']}")
        return result
    
    def get_notebook(self, args):
        logger.info(f"Getting notebook: {args.notebook_id}")
        # Placeholder: notebook = Notebook.get(args.notebook_id)
        if args.notebook_id == "nb_1":
            notebook_data = {
                'id': 'nb_1', 'name': 'Notebook 1', 'description': 'Desc 1', 'created': '2023-01-01T10:00:00', 
                'updated': '2023-01-01T11:00:00', 'archived': False,
                'sources_count': 2, 'notes_count': 5, 'chat_sessions_count': 1
            }
        elif args.notebook_id == "not_found_nb":
             raise CLINotFoundException(f"Notebook not found: {args.notebook_id}")
        else:
            raise CLINotFoundException(f"Notebook not found: {args.notebook_id}")
        
        if not args.json:
            print(f"Notebook: {notebook_data['name']} ({notebook_data['id']})")
            # ... (print other details)
        return notebook_data
    
    def create_notebook(self, args):
        logger.info(f"Creating notebook with name: {args.name}, description: {args.description}")
        if not args.name or len(args.name.strip()) == 0:
            raise CLIInvalidInputException("Notebook name cannot be empty.")
        if args.name == "error_prone_name": # Simulate a creation error
            raise CLIExecutionException("Simulated database error during notebook creation.")
        try:
            # Placeholder: notebook = Notebook(name=args.name, description=args.description); notebook.save()
            new_id = f"nb_{abs(hash(args.name)) % 1000}" # Simulate ID generation
            notebook_data = {
                'id': new_id, 'name': args.name, 'description': args.description,
                'created': '2023-01-03T12:00:00' # Simulate creation time
            }
        except Exception as e:
            logger.error(f"Failed to create notebook: {e}")
            raise CLIExecutionException(f"Database error while creating notebook: {e}")

        if not args.json:
            print(f"Created notebook: {notebook_data['id']} - {notebook_data['name']}")
        return notebook_data
    
    def archive_notebook(self, args):
        logger.info(f"Archiving notebook: {args.notebook_id}")
        # Placeholder: notebook = Notebook.get(args.notebook_id); notebook.archived = True; notebook.save()
        if args.notebook_id == "nb_1":
            result = {'id': args.notebook_id, 'name': 'Notebook 1', 'archived': True}
            if not args.json:
                print(f"Archived notebook: {result['name']} ({result['id']})")
            return result
        else:
            raise CLINotFoundException(f"Notebook not found: {args.notebook_id}")
    
    def unarchive_notebook(self, args):
        logger.info(f"Unarchiving notebook: {args.notebook_id}")
        # Placeholder: notebook = Notebook.get(args.notebook_id); notebook.archived = False; notebook.save()
        if args.notebook_id == "nb_2": # Assuming nb_2 was archived
            result = {'id': args.notebook_id, 'name': 'Archived NB', 'archived': False}
            if not args.json:
                print(f"Unarchived notebook: {result['name']} ({result['id']})")
            return result
        else:
            raise CLINotFoundException(f"Notebook not found: {args.notebook_id}")

    # === SOURCE COMMANDS (Placeholders) ===
    def list_sources(self, args):
        logger.info(f"Listing sources for notebook: {args.notebook_id}")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found or has no sources.")
        sources_data = [
            {'id': 'src_1', 'title': 'Source 1', 'type': 'text', 'created': '2023-01-01T10:05:00', 'updated': '2023-01-01T10:05:00', 'embedded_chunks': 5},
            {'id': 'src_2', 'title': 'Source URL', 'type': 'url', 'created': '2023-01-01T10:10:00', 'updated': '2023-01-01T10:10:00', 'embedded_chunks': 10}
        ]
        if not args.json: [print(f"ID: {s['id']}, Title: {s['title']}") for s in sources_data]
        return sources_data

    def get_source(self, args):
        logger.info(f"Getting source: {args.source_id}")
        if args.source_id == "src_1":
            source_data = {'id': 'src_1', 'title': 'Source 1', 'created': '2023-01-01T10:05:00', 'notebook_id': 'nb_1', 'insights_count': 2}
            if args.full_text: source_data['content'] = "This is the full text of source 1."
            if args.show_insights: source_data['insights'] = [{'id': 'ins_1', 'content': 'Insight 1'}]
            if not args.json: print(f"Source: {source_data['title']}")
            return source_data
        raise CLINotFoundException(f"Source not found: {args.source_id}")

    def add_text_source(self, args):
        logger.info(f"Adding text source '{args.title}' to notebook {args.notebook_id}")
        if not all([args.notebook_id, args.title, args.content]): raise CLIInvalidInputException("Notebook ID, title, content required.")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found.")
        new_id = f"src_{abs(hash(args.title)) % 1000}"
        result = {'id': new_id, 'title': args.title, 'notebook_id': args.notebook_id}
        if args.embed: logger.info(f"Placeholder: Embedding source {new_id}")
        if args.transform: logger.info(f"Placeholder: Applying standard transformations to {new_id}")
        elif args.apply_transformations: logger.info(f"Placeholder: Applying transformations {args.apply_transformations} to {new_id}")
        if not args.json: print(f"Added text source '{args.title}' ({new_id})")
        return result

    def add_url_source(self, args):
        logger.info(f"Adding URL source {args.url} to notebook {args.notebook_id}")
        if not all([args.notebook_id, args.url]): raise CLIInvalidInputException("Notebook ID and URL required.")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found.")
        new_id = f"src_{abs(hash(args.url)) % 1000}"
        result = {'id': new_id, 'title': args.url, 'notebook_id': args.notebook_id, 'url': args.url}
        if args.embed: logger.info(f"Placeholder: Embedding source {new_id} from URL {args.url}")
        if args.transform: logger.info(f"Placeholder: Applying standard transformations to {new_id}")
        elif args.apply_transformations: logger.info(f"Placeholder: Applying transformations {args.apply_transformations} to {new_id}")
        if not args.json: print(f"Added URL source '{args.url}' ({new_id})")
        return result

    def embed_source(self, args):
        logger.info(f"Embedding source: {args.source_id}")
        if args.source_id not in ["src_1", "src_2"]: raise CLINotFoundException(f"Source {args.source_id} not found.")
        logger.info(f"Placeholder: Embedding initiated for source {args.source_id}")
        result = {'id': args.source_id, 'status': 'embedding_initiated', 'embedded_chunks': 10} # Simulated
        if not args.json: print(f"Embedding initiated for source: {args.source_id}")
        return result

    # === NOTE COMMANDS (Placeholders) ===
    def list_notes(self, args):
        logger.info(f"Listing notes for notebook: {args.notebook_id}")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found or has no notes.")
        notes_data = [{'id': 'note_1', 'title': 'My Note', 'type': 'human'}, {'id': 'note_ai', 'title': 'AI Summary', 'type': 'ai'}]
        if not args.json: [print(f"ID: {n['id']}, Title: {n['title']}") for n in notes_data]
        return notes_data

    def get_note(self, args):
        logger.info(f"Getting note: {args.note_id}")
        if args.note_id == "note_1":
            note_data = {'id': 'note_1', 'title': 'My Note', 'content': 'This is my note.', 'type': 'human', 'notebook_id': 'nb_1'}
            if not args.json: print(f"Note: {note_data['title']}")
            return note_data
        raise CLINotFoundException(f"Note not found: {args.note_id}")

    def create_note(self, args):
        logger.info(f"Creating note '{args.title}' in notebook {args.notebook_id}")
        if not all([args.notebook_id, args.title, args.content]): raise CLIInvalidInputException("Notebook ID, title, content required.")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found.")
        new_id = f"note_{abs(hash(args.title)) % 1000}"
        result = {'id': new_id, 'title': args.title, 'notebook_id': args.notebook_id, 'type': args.type}
        if not args.json: print(f"Created {args.type} note '{args.title}' ({new_id})")
        return result

    def insight_to_note(self, args):
        logger.info(f"Converting insight {args.source_insight_id} to note in notebook {args.notebook_id}")
        if args.source_insight_id != "ins_1": raise CLINotFoundException(f"Insight {args.source_insight_id} not found.")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found.")
        new_id = f"note_from_{args.source_insight_id}"
        result = {'id': new_id, 'title': f'Note from Insight {args.source_insight_id}', 'notebook_id': args.notebook_id}
        if not args.json: print(f"Converted insight {args.source_insight_id} to note {new_id}")
        return result

    # === TRANSFORMATION COMMANDS (Placeholders) ===
    def list_transformations(self, args):
        logger.info("Listing transformations")
        trans_data = [{'id': 'trans_1', 'name': 'Summary', 'short_code': 'sum', 'apply_default': True}]
        if not args.json: [print(f"ID: {t['id']}, Name: {t['name']}") for t in trans_data]
        return trans_data

    def get_transformation(self, args):
        logger.info(f"Getting transformation: {args.transformation_id}")
        if args.transformation_id == "trans_1":
            trans_data = {'id': 'trans_1', 'name': 'Summary', 'short_code': 'sum', 'description': 'Creates a summary.', 'prompt_template': 'Summarize: {{text}}', 'apply_default': True}
            if not args.json: print(f"Transformation: {trans_data['name']}")
            return trans_data
        raise CLINotFoundException(f"Transformation not found: {args.transformation_id}")

    def create_transformation(self, args):
        logger.info(f"Creating transformation: {args.name}")
        if not all([args.name, args.short_code, args.description, args.prompt_template]): raise CLIInvalidInputException("Required fields missing.")
        new_id = f"trans_{abs(hash(args.name)) % 1000}"
        result = {'id': new_id, 'name': args.name, 'short_code': args.short_code, 'apply_default': args.apply_default}
        if not args.json: print(f"Created transformation '{args.name}' ({new_id})")
        return result

    def apply_transformation(self, args):
        logger.info(f"Applying transformation to source: {args.source_id}")
        if args.source_id not in ["src_1", "src_2"]: raise CLINotFoundException(f"Source {args.source_id} not found.")
        if not args.transform and not args.transformation_id: raise CLIInvalidInputException("Need --transform or transformation_id")
        action = "standard transformations" if args.transform else f"transformation {args.transformation_id}"
        logger.info(f"Placeholder: Applying {action} to source {args.source_id}")
        result = {'id': args.source_id, 'status': 'transformation_applied', 'insights_created_count': 1} # Simulated
        if not args.json: print(f"Transformation process initiated for source {args.source_id}")
        return result

    # === CHAT COMMANDS (Placeholders) ===
    def list_chat_sessions(self, args):
        logger.info(f"Listing chat sessions for notebook: {args.notebook_id}")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found or has no chats.")
        chat_data = [{'id': 'chat_1', 'title': 'Research Chat'}]
        if not args.json: [print(f"ID: {c['id']}, Title: {c['title']}") for c in chat_data]
        return chat_data

    def create_chat_session(self, args):
        logger.info(f"Creating chat session '{args.title}' in notebook {args.notebook_id}")
        if not all([args.notebook_id, args.title]): raise CLIInvalidInputException("Notebook ID and title required.")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found.")
        new_id = f"chat_{abs(hash(args.title)) % 1000}"
        result = {'id': new_id, 'title': args.title, 'notebook_id': args.notebook_id}
        if not args.json: print(f"Created chat session '{args.title}' ({new_id})")
        return result

    # === SEARCH COMMANDS (Placeholders) ===
    def text_search(self, args):
        logger.info(f"Text search: '{args.query}', sources: {args.source}, notes: {args.note}, results: {args.results}")
        # Placeholder: results = actual_text_search_func(...)
        sim_results = [
            {"id": "res_txt_1", "type": "source" if args.source else "note", "title": "Text Search Result 1", "score": 0.85},
            {"id": "res_txt_2", "type": "note" if args.note else "source", "title": "Text Search Result 2", "score": 0.75}
        ][:args.results]
        if not args.json: [print(f"  ID: {r['id']}, Title: {r['title']}") for r in sim_results]
        return sim_results

    def vector_search(self, args):
        logger.info(f"Vector search: '{args.query}', sources: {args.source}, notes: {args.note}, results: {args.results}, min_score: {args.min_score}")
        # Placeholder: results = actual_vector_search_func(...)
        sim_results = [
            {"id": "res_vec_1", "type": "source" if args.source else "note", "title": "Vector Search Result 1", "score": args.min_score + 0.1},
            {"id": "res_vec_2", "type": "note" if args.note else "source", "title": "Vector Search Result 2", "score": args.min_score + 0.05}
        ][:args.results]
        if not args.json: [print(f"  ID: {r['id']}, Title: {r['title']}") for r in sim_results]
        return sim_results

    # === PODCAST COMMANDS (Placeholders) ===
    def list_podcast_templates(self, args):
        logger.info("Listing podcast templates")
        tmpl_data = [{'id': 'ptmpl_1', 'name': 'Default Template'}]
        if not args.json: [print(f"ID: {t['id']}, Name: {t['name']}") for t in tmpl_data]
        return tmpl_data

    def get_podcast_template(self, args):
        logger.info(f"Getting podcast template: {args.template_id}")
        if args.template_id == "ptmpl_1":
            tmpl_data = {'id': 'ptmpl_1', 'name': 'Default Template', 'description': 'A default podcast template.'}
            if not args.json: print(f"Template: {tmpl_data['name']}")
            return tmpl_data
        raise CLINotFoundException(f"Podcast template not found: {args.template_id}")

    def list_podcast_episodes(self, args):
        logger.info(f"Listing podcast episodes, order: {args.order_by}")
        ep_data = [{'id': 'ep_1', 'name': 'Episode 1', 'status': 'completed'}]
        if not args.json: [print(f"ID: {e['id']}, Name: {e['name']}") for e in ep_data]
        return ep_data

    def generate_podcast(self, args):
        logger.info(f"Generating podcast '{args.episode_name}' from notebook {args.notebook_id} using template {args.template_id}")
        if args.notebook_id != "nb_1": raise CLINotFoundException(f"Notebook {args.notebook_id} not found.")
        if args.template_id != "ptmpl_1": raise CLINotFoundException(f"Template {args.template_id} not found.")
        new_id = f"ep_{abs(hash(args.episode_name)) % 1000}"
        result = {'id': new_id, 'name': args.episode_name, 'status': 'completed', 'audio_url': f'/simulated/{new_id}.mp3'}
        logger.info(f"Placeholder: Podcast generation for {args.episode_name} (ID: {new_id}) instructions: {args.instructions}, longform: {args.longform}")
        if not args.json: print(f"Generated podcast '{args.episode_name}' ({new_id})")
        return result

    def get_command_help(self, args):
        logger.info(f"Getting help for command: {args.subcommand_name}")
        subparser_action = next((action for action in self.parser._actions if isinstance(action, argparse._SubParsersAction)), None)
        if not subparser_action: raise CLIExecutionException("Could not find subparsers action.")
        subparser = subparser_action.choices.get(args.subcommand_name)
        if not subparser: raise CLINotFoundException(f"Command '{args.subcommand_name}' not found.")
        help_text = subparser.format_help()
        if not args.json: print(help_text)
        return {"command": args.subcommand_name, "help_text": help_text}

if __name__ == "__main__":
    # Placeholder for DB/config initialization if needed when run as script
    # try:
    #     from open_notebook.config import load_config
    #     from open_notebook.database.repository import init_db_from_config
    #     load_config()
    #     init_db_from_config()
    #     logger.info("CLI: Database and config initialized.")
    # except Exception as e:
    #     print(f"Critical error during initial setup: {e}", file=sys.stderr)
    #     sys.exit(1)
    cli = OpenNotebookCLI()
    cli.run()