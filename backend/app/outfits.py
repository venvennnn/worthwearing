"""Explicit color, layer, style, season, and occasion compatibility rules."""

from __future__ import annotations

from app.models import CompatibleOutfit, Garment, OutfitPiece, RejectedCombination

NEUTRALS = {
    "black",
    "white",
    "gray",
    "grey",
    "charcoal",
    "ivory",
    "cream",
    "beige",
    "camel",
    "navy",
    "brown",
    "taupe",
}

COLOR_FAMILIES: dict[str, set[str]] = {
    "black": {"black", "charcoal", "gray", "grey"},
    "white": {"white", "ivory", "cream"},
    "blue": {"blue", "navy", "indigo", "light-blue"},
    "brown": {"brown", "camel", "beige", "taupe", "olive"},
    "green": {"olive", "green"},
}

CLASSIC = {"classic", "tailored", "workwear", "minimal", "versatile"}
CASUAL = {"casual", "weekend", "street"}
EDGY = {"edgy", "biker", "statement", "moto"}

LAYER_ORDER = ["base", "mid", "outer", "bottom", "shoes"]


def jaccard(a: list[str] | set[str], b: list[str] | set[str]) -> float:
    left, right = set(a), set(b)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


class OutfitEngine:
    def colors_compatible(self, left: Garment, right: Garment) -> bool:
        if any(color in NEUTRALS for color in left.colors) or any(
            color in NEUTRALS for color in right.colors
        ):
            return True
        for color in left.colors:
            family = COLOR_FAMILIES.get(color, {color})
            if family & set(right.colors):
                return True
            for other in right.colors:
                if color in COLOR_FAMILIES.get(other, {other}):
                    return True
        return bool(set(left.colors) & set(right.colors))

    def styles_compatible(self, left: Garment, right: Garment) -> bool:
        ls, rs = set(left.style_tags), set(right.style_tags)
        if ls & rs:
            return True
        left_classic, right_classic = bool(ls & CLASSIC), bool(rs & CLASSIC)
        left_casual, right_casual = bool(ls & CASUAL), bool(rs & CASUAL)
        left_edgy, right_edgy = bool(ls & EDGY), bool(rs & EDGY)
        if left_classic and right_classic:
            return True
        if left_classic and right_casual:
            return True
        if left_casual and right_classic:
            return True
        if left_edgy and right_casual:
            return True
        if left_casual and right_edgy:
            return True
        if left_edgy and right_classic:
            # Edgy + strictly tailored workwear is a clash unless the classic
            # piece is also minimal/versatile and dark-neutral.
            if {"minimal", "versatile"} & rs or {"minimal", "versatile"} & ls:
                return True
            return False
        return False

    def seasons_compatible(self, left: Garment, right: Garment) -> bool:
        if not left.season_tags or not right.season_tags:
            return True
        if len(left.season_tags) >= 4 or len(right.season_tags) >= 4:
            return True
        return bool(set(left.season_tags) & set(right.season_tags))

    def occasions_overlap(self, left: Garment, right: Garment) -> set[str]:
        return set(left.occasion_tags) & set(right.occasion_tags)

    def layers_stack(self, outer: Garment, inner: Garment) -> bool:
        if outer.layer == "outer" and inner.layer in {"base", "mid"}:
            return True
        if outer.layer == "mid" and inner.layer == "base":
            return True
        return False

    def _reject(
        self,
        items: list[Garment],
        rule: str,
        reason: str,
        bucket: list[RejectedCombination],
        seen: set[tuple[str, ...]],
    ) -> None:
        key = tuple(sorted(item.id for item in items) + [rule])
        if key in seen:
            return
        seen.add(key)
        if len(bucket) >= 12:
            return
        bucket.append(
            RejectedCombination(
                item_ids=[item.id for item in items],
                names=[item.name for item in items],
                rule=rule,
                reason=reason,
            )
        )

    def build_outfits(
        self, candidate: Garment, closet: list[Garment]
    ) -> tuple[list[CompatibleOutfit], list[RejectedCombination]]:
        bases = [item for item in closet if item.layer == "base"]
        mids = [item for item in closet if item.layer == "mid"]
        bottoms = [item for item in closet if item.layer == "bottom"]
        shoes = [item for item in closet if item.layer == "shoes"]
        rejected: list[RejectedCombination] = []
        seen_reject: set[tuple[str, ...]] = set()
        outfits: list[CompatibleOutfit] = []

        def pair_ok(left: Garment, right: Garment) -> tuple[bool, str, str]:
            if not self.colors_compatible(left, right):
                return False, "color", f"{left.name} clashes with {right.name}."
            if not self.styles_compatible(left, right):
                return False, "style", f"{left.name} style does not sit with {right.name}."
            if not self.seasons_compatible(left, right):
                return False, "season", f"{left.name} and {right.name} do not share a season."
            if not self.occasions_overlap(left, right):
                return False, "occasion", f"{left.name} and {right.name} share no occasion."
            return True, "", ""

        for base in bases:
            ok, rule, reason = pair_ok(candidate, base)
            if not ok:
                self._reject([candidate, base], rule, reason, rejected, seen_reject)
                continue
            if candidate.layer == "outer" and not self.layers_stack(candidate, base):
                self._reject(
                    [candidate, base],
                    "layer",
                    f"{base.name} cannot layer under {candidate.name}.",
                    rejected,
                    seen_reject,
                )
                continue
            for bottom in bottoms:
                ok_b, rule_b, reason_b = pair_ok(candidate, bottom)
                if not ok_b:
                    self._reject(
                        [candidate, bottom], rule_b, reason_b, rejected, seen_reject
                    )
                    continue
                ok_bb, rule_bb, reason_bb = pair_ok(base, bottom)
                if not ok_bb:
                    self._reject(
                        [base, bottom], rule_bb, reason_bb, rejected, seen_reject
                    )
                    continue
                shared = (
                    self.occasions_overlap(candidate, base)
                    & self.occasions_overlap(candidate, bottom)
                )
                if not shared:
                    self._reject(
                        [candidate, base, bottom],
                        "occasion",
                        "No shared occasion across jacket, top, and bottom.",
                        rejected,
                        seen_reject,
                    )
                    continue
                occasion = sorted(shared)[0]
                pieces = [
                    OutfitPiece(
                        item_id=candidate.id,
                        name=candidate.name,
                        image_url=candidate.image_url,
                        layer=candidate.layer,
                    ),
                    OutfitPiece(
                        item_id=base.id,
                        name=base.name,
                        image_url=base.image_url,
                        layer=base.layer,
                    ),
                    OutfitPiece(
                        item_id=bottom.id,
                        name=bottom.name,
                        image_url=bottom.image_url,
                        layer=bottom.layer,
                    ),
                ]
                shoe = next(
                    (
                        s
                        for s in shoes
                        if pair_ok(candidate, s)[0]
                        and pair_ok(bottom, s)[0]
                        and self.occasions_overlap(s, candidate) & shared
                    ),
                    None,
                )
                if shoe:
                    pieces.append(
                        OutfitPiece(
                            item_id=shoe.id,
                            name=shoe.name,
                            image_url=shoe.image_url,
                            layer=shoe.layer,
                        )
                    )
                outfits.append(
                    CompatibleOutfit(
                        id=f"{candidate.id}-{base.id}-{bottom.id}",
                        occasion=occasion,
                        pieces=pieces,
                        rationale=(
                            f"{base.name} and {bottom.name} share color, season, and "
                            f"{occasion} with {candidate.name}."
                        ),
                    )
                )

        # Optional mid-layer outfits that do not duplicate a counted pair.
        existing_pairs = {(o.pieces[1].item_id, o.pieces[2].item_id) for o in outfits}
        for mid in mids:
            ok, rule, reason = pair_ok(candidate, mid)
            if not ok:
                self._reject([candidate, mid], rule, reason, rejected, seen_reject)
                continue
            for base in bases:
                if not self.layers_stack(mid, base):
                    continue
                ok_m, _, _ = pair_ok(mid, base)
                if not ok_m:
                    continue
                for bottom in bottoms:
                    pair = (base.id, bottom.id)
                    if pair in existing_pairs:
                        continue
                    ok_b, _, _ = pair_ok(candidate, bottom)
                    ok_mb, _, _ = pair_ok(mid, bottom)
                    if not (ok_b and ok_mb):
                        continue
                    shared = (
                        self.occasions_overlap(candidate, mid)
                        & self.occasions_overlap(mid, base)
                        & self.occasions_overlap(candidate, bottom)
                    )
                    if not shared:
                        continue
                    outfits.append(
                        CompatibleOutfit(
                            id=f"{candidate.id}-{mid.id}-{base.id}-{bottom.id}",
                            occasion=sorted(shared)[0],
                            pieces=[
                                OutfitPiece(
                                    item_id=candidate.id,
                                    name=candidate.name,
                                    image_url=candidate.image_url,
                                    layer=candidate.layer,
                                ),
                                OutfitPiece(
                                    item_id=mid.id,
                                    name=mid.name,
                                    image_url=mid.image_url,
                                    layer=mid.layer,
                                ),
                                OutfitPiece(
                                    item_id=base.id,
                                    name=base.name,
                                    image_url=base.image_url,
                                    layer=base.layer,
                                ),
                                OutfitPiece(
                                    item_id=bottom.id,
                                    name=bottom.name,
                                    image_url=bottom.image_url,
                                    layer=bottom.layer,
                                ),
                            ],
                            rationale=(
                                f"{mid.name} layers over {base.name} for a "
                                f"{sorted(shared)[0]} look with {candidate.name}."
                            ),
                        )
                    )

        outfits.sort(key=lambda o: (o.occasion, o.id))
        return outfits, rejected
