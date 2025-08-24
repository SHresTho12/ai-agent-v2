import asyncio
import click
import logging


from .core.llm_client import LLMClient
from .core.tool_registry import ToolRegistry
from .core.tool_executor import ToolExecutor
# from .tools.registry import register_tool


logger = logging.getLogger(__name__)


@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
def main(interactive: bool):

    if interactive:
        logger.info("Starting interactive mode...")
        # Implement interactive mode logic here
    else:
        logger.info("Starting normal mode...")
    
    
    registry = ToolRegistry()
    # register_tool(registry)

    llm_client = LLMClient()
    tool_executor = ToolExecutor(tool_registry=registry)
    
    
    
    if interactive:
        print("Interactive mode is not yet implemented.")
        pass
    else:
        user_input = click.prompt("Enter your request")
        asyncio.run(process_single_request(user_input, llm_client, tool_executor, registry))



# async def interactive_mode(llm_client, tool_executor, registry):
#     """Interactive chat mode"""
#     click.echo("Welcome to LLM Tool Caller! Type 'exit' to quit.")
    
#     while True:
#         user_input = click.prompt("\n> ")
        
#         if user_input.lower() in ['exit', 'quit']:
#             break
        
#         try:
#             await process_single_request(user_input, llm_client, tool_executor, registry)
#         except Exception as e:
#             logger.error(f"Error processing request: {e}")
#             click.echo(f"Error: {e}")

async def process_single_request(user_input, llm_client, tool_executor, registry):
    """Process a single user request"""
    
    # Get available tools
    tool_schemas = registry.get_all_schemas()
    
    # Process with LLM
    llm_response = await llm_client.process_user_input(user_input, tool_schemas)
    
    if llm_response.tool_calls:
        execution_results = await tool_executor.execute_tool_calls(llm_response.tool_calls)
        
        # Generate final response
        final_response = await llm_client.generate_final_response(user_input, execution_results)
        click.echo(final_response)
    else:
        click.echo(llm_response.content)

if __name__ == "__main__":
    main()
