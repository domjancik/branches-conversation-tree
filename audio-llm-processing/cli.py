import click
from image_prompt_generation import get_image_prompts
import os

@click.group()
def cli():
    """CLI for audio-llm-processing service"""
    pass

@cli.command()
@click.argument('text', required=False)
@click.option('--input-file', '-i', type=click.Path(exists=True), help='Path to file containing input text')
@click.option('--model', default='gemma2:2b', help='Ollama model to use for generation')
@click.option('--prompt-count', default=6, help='Number of prompts to generate')
@click.option('--max-retries', default=4, help='Maximum number of retries for failed generations')
def generate_image_prompts(text, input_file, model, prompt_count, max_retries):
    """Generate image prompts from the given text using the specified model.
    
    You can provide the text directly as an argument or specify a file path using --input-file.
    If both are provided, the file content takes precedence.
    """
    try:
        if input_file:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
        elif not text:
            raise click.UsageError("Either text argument or --input-file must be provided")

        prompts = get_image_prompts(
            text=text,
            ollama_model=model,
            prompt_count=prompt_count,
            max_retries=max_retries
        )
        click.echo("Generated prompts:")
        for i, prompt in enumerate(prompts, 1):
            click.echo(f"{i}. {prompt}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli() 