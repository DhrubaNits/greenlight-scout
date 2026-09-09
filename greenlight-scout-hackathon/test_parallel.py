from parallel import Parallel

client = Parallel()

search = client.search(
    objective=(
        "Find current and reliable information about filming permits, "
        "drone filming restrictions, and temporary road closure requirements "
        "for a professional film production in central London. "
        "Prefer official authorities and film commission sources."
    ),
    search_queries=[
        "London filming permit requirements",
        "London drone filming rules",
        "London filming road closures",
    ],
)

print("\n=== PARALLEL SEARCH RESULTS ===\n")

for i, result in enumerate(search.results, start=1):
    print(f"RESULT {i}")
    print("Title:", result.title)
    print("URL:", result.url)
    print("Publish date:", result.publish_date)

    print("Excerpts:")
    for excerpt in result.excerpts:
        print("-", excerpt[:800])

    print("\n" + "-" * 80 + "\n")