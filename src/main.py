"""Main entry point for Bakery Quotation Agent"""
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from src.agent import BakeryQuotationAgent
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)
console = Console()


def main():
    """Main entry point"""
    try:
        # Load configuration
        console.print("\n[yellow]Loading configuration...[/yellow]")
        config = Config.from_env()
        config.validate()
        console.print("[green]✓ Configuration loaded[/green]")

        # Display banner
        console.print(Panel.fit(
            "[bold cyan]Bakery Quotation Agent v1.0[/bold cyan]\n"
            f"Powered by {config.model_name}",
            border_style="cyan"
        ))

        # Initialize agent
        console.print("\n[yellow]Initializing agent...[/yellow]")
        agent = BakeryQuotationAgent(config)
        console.print("[green]✓ Agent initialized[/green]\n")

        # Start interactive loop
        run_interactive(agent)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {str(e)}[/red]")
        logger.error("Fatal error", exc_info=True)
        sys.exit(1)


def run_interactive(agent: BakeryQuotationAgent):
    """Run agent in interactive CLI mode"""

    console.print("[bold]Agent:[/bold] Hello! I'll help you create a bakery quotation.\n")

    while True:
        try:
            # Get user input
            user_input = console.input("[bold blue]You:[/bold blue] ").strip()

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                console.print("\n[cyan]Thank you for using the Bakery Quotation Agent![/cyan]")
                break

            # Check for reset command
            if user_input.lower() in ['reset', 'restart', 'new']:
                agent.reset()
                console.print("\n[green]✓ Agent reset. Starting fresh![/green]\n")
                console.print("[bold]Agent:[/bold] Let's create a new quotation. What can I help you with?\n")
                continue

            # Invoke agent
            console.print()  # Blank line before response
            with console.status("[yellow]Agent thinking...[/yellow]", spinner="dots"):
                response = agent.invoke(user_input)

            # Display agent response
            console.print(f"[bold]Agent:[/bold] {response['output']}\n")

            # Check if quote is complete
            if "Quote Generated Successfully" in response['output']:
                console.print("[green]✨ Quote generation complete![/green]\n")

                again = console.input(
                    "[bold]Would you like to create another quote? (yes/no):[/bold] "
                ).strip().lower()

                if again in ['yes', 'y']:
                    agent.reset()
                    console.print("\n" + "━" * 60 + "\n")
                    console.print("[bold]Agent:[/bold] Let's create a new quotation!\n")
                else:
                    console.print("\n[cyan]Thank you! Goodbye![/cyan]")
                    break

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type 'exit' to quit or continue chatting.[/yellow]\n")
        except Exception as e:
            console.print(f"\n[red]Error: {str(e)}[/red]\n")
            logger.error("Error in conversation loop", exc_info=True)


if __name__ == "__main__":
    main()
