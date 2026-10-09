# 2–3 minute demo outline

## 0:00–0:20 — Problem

Christian: A quantum system can drift away from the Hamiltonian we think we programmed. Measuring everything is expensive, so the useful question is not only “what changed?” but “what should we measure next?”

## 0:20–0:40 — Setup

Show the four-qubit TFIM and the nominal couplings. Secretly change one coupling with the demo config/UI.

## 0:40–1:35 — Diagnosis

Dobromir: Run Q-Scope. Show the chosen initial state, time, observable, measurement result, and posterior estimate after each step. Explain that candidate models disagree differently on different experiments, so Q-Scope chooses the experiment with highest expected information gain.

## 1:35–2:10 — Reveal

Show the hidden coupling and Q-Scope's estimate. Show the nominal/hidden/estimated parameter figure.

## 2:10–2:40 — Benchmark

Alex: Show error vs experiment number for active, random, and fixed strategies. State the actual measured headline result from the benchmark artifact.

## 2:40–3:00 — Close

The idea: instead of measuring everything, Q-Scope learns what to measure next. Mention that the full judged path runs locally in Qiskit and is reproducible from the public MIT-licensed repository.
