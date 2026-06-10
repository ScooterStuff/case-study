import React from "react";
import { render, screen } from "@testing-library/react";
import ProductCard from "../ProductCard";
import CompatResult from "../CompatResult";
import Diagnosis from "../Diagnosis";
import { CartProvider } from "../../../context/CartContext";

const product = {
  ps_number: "PS3406971", mpn: "W10195416", brand: "Whirlpool",
  title: "Lower Dishrack Wheel", price: 32.91, availability: "In Stock",
  install_difficulty: "Very Easy", rating: 4.8, review_count: 406,
  image_url: "http://example.com/x.jpg", product_url: "http://example.com",
};

const wrap = (ui) => render(<CartProvider>{ui}</CartProvider>);

test("ProductCard shows price, stock badge and difficulty chip", () => {
  wrap(<ProductCard product={product} />);
  expect(screen.getByText("$32.91")).toBeInTheDocument();
  expect(screen.getByText("In Stock")).toBeInTheDocument();
  expect(screen.getByText(/Very Easy install/)).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /Lower Dishrack Wheel/ })).toBeInTheDocument();
});

test("CompatResult verified_fit shows teal check and evidence", () => {
  wrap(<CompatResult block={{ verdict: "verified_fit", part: "PS3406971",
                              model: "WDT780SAEM1", evidence_count: 12 }} />);
  expect(screen.getByText("Verified fit")).toBeInTheDocument();
  expect(screen.getByText("✓")).toBeInTheDocument();
  expect(screen.getByText(/12 models including yours/)).toBeInTheDocument();
});

test("CompatResult no_match_found shows the honesty note, never a hard no", () => {
  wrap(<CompatResult block={{ verdict: "no_match_found", part: "PS11752778",
                              model: "WDT780SAEM1", evidence_count: 233,
                              honesty_note: "Not in our verified list - partial data." }} />);
  expect(screen.getByText("Not in our verified list")).toBeInTheDocument();
  expect(screen.getByText("⚠")).toBeInTheDocument();
  expect(screen.getByText(/doesn't necessarily mean it won't fit/)).toBeInTheDocument();
});

test("Diagnosis renders causes in rank order with suggested parts", () => {
  wrap(<Diagnosis block={{
    causes: [{ rank: 1, cause: "Water Fill Tubes" }, { rank: 2, cause: "Water Inlet Valve" }],
    suggested_parts: [product],
  }} />);
  const items = screen.getAllByRole("listitem").map((li) => li.textContent);
  expect(items[0]).toMatch(/1.*Water Fill Tubes/);
  expect(items[1]).toMatch(/2.*Water Inlet Valve/);
  expect(screen.getByText("Lower Dishrack Wheel")).toBeInTheDocument();
});
