"""
Quick Start: Real Logo Generation with DALL-E
==============================================

This is your FIRST REAL TASK EXECUTION example.
Install, configure, and watch your agent generate an actual logo.

Setup Time: 5 minutes
Cost: $0.04 per logo
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def generate_logo_quick_start():
    """
    Quick start example: Generate a real logo using DALL-E

    This demonstrates:
    1. API integration (OpenAI)
    2. Cost tracking ($0.04/image)
    3. Real deliverable output
    """

    print("\n" + "=" * 80)
    print("🎨 QUICK START: REAL LOGO GENERATION")
    print("=" * 80)

    # Step 1: Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not found in .env file")
        print("\n📝 Setup Instructions:")
        print("1. Get your API key: https://platform.openai.com/api-keys")
        print("2. Add to .env file:")
        print("   OPENAI_API_KEY=sk-proj-your-key-here")
        print("3. Run this script again")
        return

    print(f"\n✅ API Key found: {api_key[:20]}...")

    # Step 2: Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client initialized")

    # Step 3: Define logo concept
    company_name = "Surfacecraft Studio"
    industry = "Granite & Countertop Installation"

    prompt = f"""Modern, professional logo for {company_name}, a premium {industry} company.

Design requirements:
- Clean, minimalist aesthetic
- Incorporates geometric shapes or stone texture
- Navy blue (#1A365D) and warm gray color palette
- Suitable for both digital and print (scalable)
- Conveys craftsmanship, quality, and precision

Style: Modern, professional, memorable
NO TEXT in the logo design - symbol/icon only"""

    print(f"\n📋 Logo Brief:")
    print(f"   Company: {company_name}")
    print(f"   Industry: {industry}")
    print(f"   Style: Modern, minimalist")
    print(f"   Colors: Navy blue + warm gray")

    # Step 4: Generate logo
    print(f"\n🎨 Generating logo with DALL-E 3...")
    print(f"   Cost: $0.04 (standard quality, 1024x1024)")

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",  # "hd" costs $0.08
            n=1,
        )

        # Step 5: Get result
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        print("\n✅ Logo generated successfully!")
        print(f"\n🖼️  Image URL:")
        print(f"   {image_url}")
        print(f"\n📝 DALL-E refined your prompt to:")
        print(f"   {revised_prompt}")

        # Step 6: Show next steps
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! Your agent just executed its first real-world task!")
        print("=" * 80)

        print("\n📊 Task Summary:")
        print(f"   ✅ Task: Logo generation")
        print(f"   ✅ Tool: OpenAI DALL-E 3")
        print(f"   ✅ Cost: $0.04")
        print(f"   ✅ Output: {image_url[:50]}...")

        print("\n📥 Download Your Logo:")
        print(f"   1. Open URL in browser: {image_url}")
        print(f"   2. Right-click → Save Image As...")
        print(f"   3. Save as: surfacecraft_logo_v1.png")

        print("\n🚀 Next Steps:")
        print("   1. Review the logo design")
        print("   2. Generate variations (run script again)")
        print("   3. Integrate into your Branding Agent")
        print("   4. Add more tools (email, social media, etc.)")

        print("\n💡 Pro Tips:")
        print("   • Edit the prompt above to generate different styles")
        print("   • Change 'modern' to 'vintage', 'minimalist', 'bold', etc.")
        print("   • Try different color palettes")
        print("   • Use quality='hd' for higher resolution ($0.08)")

        return {
            "success": True,
            "image_url": image_url,
            "revised_prompt": revised_prompt,
            "cost": 0.04,
        }

    except Exception as e:
        print(f"\n❌ Error generating logo: {str(e)}")
        print("\n🔍 Common Issues:")
        print("   • Invalid API key")
        print("   • Insufficient credits")
        print("   • Rate limit exceeded")
        print("   • Network connection")
        return {"success": False, "error": str(e), "cost": 0.0}


def batch_generate_logos(count=4):
    """
    Generate multiple logo concepts

    Args:
        count: Number of concepts to generate (1-4 recommended)
    """
    print(f"\n🎨 Generating {count} logo concepts...")
    print(f"   Total cost: ${0.04 * count}")

    results = []
    for i in range(count):
        print(f"\n--- Concept {i+1}/{count} ---")
        result = generate_logo_quick_start()
        results.append(result)

    print("\n" + "=" * 80)
    print(f"✅ Generated {count} logo concepts")
    print("=" * 80)

    successful = [r for r in results if r["success"]]
    total_cost = sum(r["cost"] for r in results)

    print(f"\n📊 Summary:")
    print(f"   Successful: {len(successful)}/{count}")
    print(f"   Total cost: ${total_cost}")

    if successful:
        print(f"\n🖼️  Your logos:")
        for i, result in enumerate(successful, 1):
            print(f"   {i}. {result['image_url']}")

    return results


if __name__ == "__main__":
    # Run the quick start
    result = generate_logo_quick_start()

    # Optionally, generate multiple concepts
    # Uncomment to generate 4 logo concepts at once ($0.16 total):
    # batch_generate_logos(count=4)
