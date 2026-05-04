#!/usr/bin/env python3
"""
ATLAS Hook Text Patcher
Replaces the hook field for all 30 sites exactly as specified.
"""

import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"

# New hook text keyed by site id — preserved exactly as given
HOOKS = {
    "stonehenge": (
        "Stones dragged from 150 miles away and joined with a precision that belongs in "
        "carpentry, not geology. We have been standing inside this circle for 5,000 years "
        "and still cannot say, with confidence, what we are standing in."
    ),
    "machupicchu": (
        "8,000 feet up, on a ridge between two peaks. Granite cut so tightly that five "
        "centuries of earthquakes couldn't find a seam to split. The Spanish never found "
        "it. The jungle couldn't take it. And the people who built it left no single "
        "explanation for what this place was meant to be."
    ),
    "giza": (
        "Press your palm against the joint between two blocks and feel how little space "
        "your doubt has left to live in. Two centimeters of error across thirteen acres. "
        "Aligned to true north with unnerving precision. 4,500 years old. The best answer "
        "anyone has still starts with \"probably.\""
    ),
    "teotihuacan": (
        "A city of 200,000 people, aligned to a point in the sky no one has identified, "
        "built by a civilization that vanished so completely we don't know their name, "
        "their language, or what they were aiming at. Even the Aztecs, who found it "
        "centuries later, had no idea. They just called it the place where the gods were "
        "born. They were guessing too."
    ),
    "gobekli-tepe": (
        "Before wheat. Before pottery. Before anyone was supposed to be capable of this. "
        "Fifteen-ton pillars, carved and raised by people who still hunted their "
        "dinner—and every new discovery pushes the mystery further back into a past we "
        "thought was empty."
    ),
    "petra": (
        "Carved from the top of a cliff downward, in a canyon with no water, by people who "
        "engineered a hydraulic system out of a desert."
    ),
    "angkor-wat": (
        "The jungle spent centuries trying to swallow it. It failed. What it couldn't "
        "digest was a temple where nothing appears accidental — alignments that track the "
        "equinox, dimensions that echo Hindu cosmology, a moat shaped like the cosmic "
        "ocean. Whether it all means what it seems to mean is the question no one has "
        "closed."
    ),
    "nazca": (
        "They drew pictures for an audience that shouldn't exist. Figures so vast you can "
        "only see them from the sky, carved into a desert floor centuries before anyone "
        "could fly. Either they were speaking to their gods — or they could see what we "
        "couldn't."
    ),
    "borobudur": (
        "72 stone bells, each hiding a Buddha you can only glimpse through diamond-shaped "
        "holes. 2,672 relief panels telling a single story across four kilometers of "
        "carved wall. Then a volcano buried it all under ash and the world forgot it for a "
        "thousand years. The story kept going. Nobody was there to read it."
    ),
    "chichen-itza": (
        "A stone machine that uses shadows to summon a serpent down the staircase on the "
        "equinox. Clap your hands at the base and it answers you in the voice of a sacred "
        "bird. This is not a building. It's a performance that's been running for a "
        "thousand years."
    ),
    "karnak": (
        "They built Karnak for two thousand years and still left it feeling unfinished—as "
        "if the complex was never meant to be completed, only fed. Walk into the Hypostyle "
        "Hall and the question isn't how they built it. It's what kind of world thought "
        "this was necessary."
    ),
    "palenque": (
        "A hidden staircase. Eighty feet straight down into the dark. A tomb sealed for "
        "1,300 years. And on the lid, a carved image so unsettling it launched a war of "
        "interpretation that still hasn't produced a winner."
    ),
    "derinkuyu": (
        "An 18-story city buried beneath the earth, sealed by half-ton stone doors that "
        "only close from the inside. This was not a hiding place. It was a world built on "
        "the assumption that whatever was above might come looking."
    ),
    "tiwanaku": (
        "Run a machinist's straight edge along the cut surface. No gap. Run your finger "
        "across the joints. Seamless. Something happened here that doesn't fit inside the "
        "story we tell about the past."
    ),
    "newgrange": (
        "Once a year, for seventeen minutes, sunlight enters a passage and touches a wall "
        "that has been waiting in darkness for five thousand years. Whoever aimed this "
        "building at that exact moment in time did not miss."
    ),
    "ellora": (
        "They didn't build it. They released it. A temple carved out of a mountain the way "
        "a sculptor pulls a figure from marble. No margin for error. No second attempt."
    ),
    "skara-brae": (
        "On a tiny island in the North Atlantic, a storm tore open a sand dune and exposed "
        "a village older than the pyramids. Stone furniture. Indoor drainage. Covered "
        "passageways. Built by people we are told had nothing."
    ),
    "dendera": (
        "At Dendera, the ceiling tracks the heavens and the crypts descend into something "
        "far stranger than decoration. The deeper you look, the more the temple begins to "
        "feel like a sealed archive of knowledge—preserved in stone long after the "
        "language needed to explain it was lost."
    ),
    "rosslyn-chapel": (
        "Every arch, pillar, and ceiling detail seems to murmur that something was hidden "
        "here on purpose — not in the crude sense of treasure, but in the older, more "
        "dangerous sense of knowledge."
    ),
    "ggantija": (
        "Older than Stonehenge. Older than the pyramids. Legend has it that a giantess "
        "built them while nursing her child. That sounds like a myth — until you stand in "
        "front of the stones and realize nobody's offered a better explanation."
    ),
    "hal-saflieni": (
        "Stand in the Oracle Chamber and speak. The sound won't echo. It will enter the "
        "limestone and come back through your chest. Three stories carved beneath the "
        "earth five thousand years ago, tuned to a frequency that resonates with the human "
        "body. Whether they understood what they were doing or stumbled into something we "
        "still can't explain — either answer is unsettling."
    ),
    "poverty-point": (
        "In Louisiana, 3,500 years ago, people we call hunter-gatherers moved more earth "
        "than most ancient cities contain. Concentric rings. Deliberate geometry. No "
        "agriculture, no cities, no civilization as we define it. Maybe the definition is "
        "the problem."
    ),
    "karahan-tepe": (
        "Gobekli Tepe was supposed to be the exception. Then they found Karahan Tepe—same "
        "age, same impossible stonework, but stranger: pillars carved from bedrock, a "
        "human head emerging from the floor, an underground chamber that feels more like "
        "an interface than a temple. One anomaly is an outlier. This many is a problem for "
        "the timeline itself."
    ),
    "longyou": (
        "A farmer draining a pond uncovered a doorway into something that shouldn't exist. "
        "Twenty-four massive caverns carved from solid sandstone, every surface grooved "
        "with inhuman precision. No record. No legend. No memory. Someone hollowed out a "
        "mountain and then history swallowed the evidence whole."
    ),
    "chavin": (
        "This temple wasn't built to be looked at. It was built to be felt. Water roaring "
        "through hidden channels. Wind howling through stone throats. The building itself "
        "was the ceremony — designed to disorient, overwhelm, and terrify anyone who "
        "walked inside."
    ),
    "saqsaywaman": (
        "Monstrous blocks fitted with a precision that unsettles our modern assumptions. "
        "No mortar. No tools we can identify. No easy explanations. Just massive, "
        "interlocking geometry staring at you — waiting for someone to explain how."
    ),
    "hampi": (
        "Strike a pillar and it sings. A different note from the one beside it. Someone "
        "looked at granite and heard music inside it. Next to it, a stone chariot with "
        "wheels that once turned. Hampi isn't a ruin. It's an instrument we forgot how to "
        "play."
    ),
    "mohenjo-daro": (
        "Mohenjo-daro should not feel this modern. Gridded streets, standardized bricks, "
        "and a drainage system older than most civilizations by millennia—then a script "
        "nobody can read and a people who vanished without leaving us the words to explain "
        "what they had built."
    ),
    "goseck": (
        "Two gates in a timber circle, both aimed at the winter solstice — not roughly, "
        "not approximately, but with a precision that turns coincidence into intention. "
        "Seven thousand years ago, someone was reading the sky like a clock. We just found "
        "the clock."
    ),
    "great-zimbabwe": (
        "Walls that rise eleven meters without a single drop of mortar, raised by a "
        "civilization so advanced that when Europeans found them, they couldn't accept the "
        "truth. They invented every theory except the obvious one. The walls don't care. "
        "They're still standing."
    ),
}


def escape_for_js(text):
    """Escape text for embedding inside a JS double-quoted string."""
    return text.replace('\\', '\\\\').replace('"', '\\"')


def patch_hook(js_text, site_id, new_hook):
    """
    Find the site entry for site_id and replace its hook field value.
    The hook field looks like:  hook: "...existing text...",
    We locate the site block first, then replace only within it.
    """
    site_pattern = re.compile(
        r'(  \{[^{]*?id:\s*"' + re.escape(site_id) + r'".*?  \},)',
        re.DOTALL
    )
    match = site_pattern.search(js_text)
    if not match:
        print(f"  ERROR: site entry not found for '{site_id}'")
        return js_text, False

    site_block = match.group(1)

    # Replace the hook value inside the block
    hook_pattern = re.compile(r'(    hook:\s*)"[^"]*"', re.DOTALL)
    escaped = escape_for_js(new_hook)
    new_site_block, count = hook_pattern.subn(rf'\1"{escaped}"', site_block)

    if count == 0:
        print(f"  ERROR: hook field not found in entry for '{site_id}'")
        return js_text, False

    return js_text[:match.start()] + new_site_block + js_text[match.end():], True


def main():
    print("=" * 60)
    print("ATLAS Hook Text Patcher — 30 sites")
    print("=" * 60)
    print()

    with open(SITES_JS, 'r', encoding='utf-8') as f:
        js_text = f.read()

    success = []
    failed  = []

    for site_id, new_hook in HOOKS.items():
        js_text, ok = patch_hook(js_text, site_id, new_hook)
        if ok:
            print(f"  [OK]  {site_id}")
            success.append(site_id)
        else:
            print(f"  [FAIL] {site_id}")
            failed.append(site_id)

    with open(SITES_JS, 'w', encoding='utf-8') as f:
        f.write(js_text)

    print()
    print("=" * 60)
    print(f"Done — {len(success)} updated, {len(failed)} failed")
    if failed:
        print(f"Failed: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
