# Original author: Mohamed Siala (Stockholm University, 2026).
# The originla code was provided for a research project in the frame of
# the MSc course Research Topics in Data Science.

# Modifications by Irina V. Demina ("IVD" below), 2026:
#   - Added the seed parameter to Model.compress() to shuffle the order of rules and literals.
#   - Added Model.compress_with_seeds() to compare compressed models across shuffles.

"""Load and check propositional models.

model = Model.from_files("examples/demo-credit-crossed.rules", "examples/background2.bk")
model.check_satisfiability()
model.check_all_overlaps()
model.check_all_redundancies()
model.check_all_literal_redundancies()
model.compress()
"""

import json
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

from pysat.formula import IDPool
from pysat.solvers import Solver

import copy
import random 

class Literal:
    def __init__(self, attribute, operator, value):
        self.attribute = attribute
        self.operator = operator
        self.value = value


class Rule:
    def __init__(self, identifier, cube, outcome):
        self.identifier = identifier
        self.cube = cube
        self.outcome = outcome


def _rule_key(rule):
    prefix = rule.identifier.rstrip("0123456789")
    return prefix, int(rule.identifier[len(prefix):] or 0), rule.identifier


@dataclass
class BackgroundKnowledge:
    clauses: list[set[Literal]] = field(default_factory=list)


def _name(text):
    return bool(text) and not any(c.isspace() or c in '()=,"' for c in text)


def _value(text):
    if text.startswith('"'):
        value, end = json.JSONDecoder().raw_decode(text)
        return value, text[end:]
    end = next((i for i, c in enumerate(text) if c in '),'), len(text))
    value = text[:end]
    if not value or any(c.isspace() or c in '("' for c in value):
        raise ValueError("invalid value")
    return value, text[end:]


def _literals(text, separator):
    literals = []
    while True:
        if not text.startswith('('):
            raise ValueError("expected '('")
        attribute, operator, text = text[1:].split(' ', 2)
        if not _name(attribute) or operator not in ('=', '!=', '<', '<=', '>', '>='):
            raise ValueError("invalid literal")
        value, text = _value(text)
        if not text.startswith(')'):
            raise ValueError("expected ')'")
        literals.append(Literal(attribute, operator, value))
        text = text[1:]
        if not text.startswith(separator):
            return literals, text
        text = text[len(separator):]


def _rule(text):
    identifier, text = text.split(' = (', 1)
    if not _name(identifier):
        raise ValueError("invalid rule identifier")
    if text.startswith('()'):
        cube, text = [], text[2:]
    else:
        cube, text = _literals(text, ' and ')
    if not text.startswith(', '):
        raise ValueError("expected ', '")
    outcome, text = _value(text[2:])
    if text != ')':
        raise ValueError("expected final ')'")
    return Rule(identifier, cube, outcome)


def _clause(text):
    literals, text = _literals(text, ' or ')
    if text:
        raise ValueError("invalid clause")
    return set(literals)


def _read(path, parse):
    result, identifiers = [], set()
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").split('\n'), 1):
        if line == '' or line.startswith('c '):
            continue
        try:
            item = parse(line)
            if isinstance(item, Rule):
                if item.identifier in identifiers:
                    raise ValueError(f"duplicate rule identifier {item.identifier}")
                identifiers.add(item.identifier)
            result.append(item)
        except ValueError as error:
            raise ValueError(f"{path}:{number}: {error}") from error
    return result


def check_model_syntax(path):
    return _read(path, _rule)


def check_background_syntax(path):
    return _read(path, _clause)


@dataclass
class Model:
    background: BackgroundKnowledge
    rules: set[Rule]

    @classmethod
    def from_files(cls, model_path, background_path=None):
        source = "background"
        try:
            if background_path:
                clauses = check_background_syntax(background_path)
                print("background syntax verified")
            else:
                clauses = []
                print("no background knowledge given")
            source = "rules"
            rules = set(check_model_syntax(model_path))
            print("rules syntax verified")
        except (ValueError, OSError) as error:
            raise SystemExit(f"{source} syntax failed: {error}") from None
        return cls(BackgroundKnowledge(clauses), rules)

    def _encode(self, rules):
        pool = IDPool()

        def encode(literal):
            operator, value, sign = literal.operator, literal.value, 1
            complements = {"!=": "=", ">=": "<", ">": "<="}
            if operator in complements:
                operator, sign = complements[operator], -sign
            return sign * pool.id((literal.attribute, operator, value))

        clauses = [[encode(lit) for lit in clause] for clause in self.background.clauses]
        cubes = [[encode(lit) for lit in rule.cube] for rule in rules]
        return clauses, cubes

    def check_satisfiability(self):
        rules = sorted(self.rules, key=lambda r: r.identifier)
        clauses, cubes = self._encode(rules)
        with Solver(bootstrap_with=clauses) as solver:
            if not solver.solve():
                print("Background: UNSAT")
                return
            print("Background: SAT")
            for rule, cube in zip(rules, cubes):
                satisfiable = solver.solve(assumptions=cube)
                print(f"{rule.identifier}: {'SAT' if satisfiable else 'UNSAT'}")

    def check_overlap(self, rule1, rule2):
        clauses, cubes = self._encode([rule1, rule2])
        with Solver(bootstrap_with=clauses) as solver:
            overlap = solver.solve(assumptions=list(set(cubes[0] + cubes[1])))
        print(f"Overlap {rule1.identifier}, {rule2.identifier}: {'yes' if overlap else 'no'}")

    def check_all_overlaps(self):
        for rule1, rule2 in combinations(sorted(self.rules, key=lambda r: r.identifier), 2):
            self.check_overlap(rule1, rule2)

    def check_redundancy(self, rule):
        if rule not in self.rules:
            raise ValueError("rule does not belong to this model")
        others = [r for r in self.rules if r is not rule and r.outcome == rule.outcome]
        clauses, cubes = self._encode([rule] + others)
        clauses += [[-literal for literal in cube] for cube in cubes[1:]]
        with Solver(bootstrap_with=clauses) as solver:
            redundant = not solver.solve(assumptions=list(set(cubes[0])))
        print(f"{rule.identifier}: {'redundant' if redundant else 'not redundant'}")

    # [Added by IVD] the same test as in check_redundancy(), but silent (no print) - 
    # returns True or False; used below for remove_redundant_literals()
    def _is_redundant(self, rule):
        others = [r for r in self.rules if r is not rule and r.outcome == rule.outcome]
        clauses, cubes = self._encode([rule] + others)
        clauses += [[-lit for lit in cube] for cube in cubes[1:]]
        with Solver(bootstrap_with=clauses) as solver:
            return not solver.solve(assumptions=list(set(cubes[0])))
        
    def check_all_redundancies(self):
        for rule in sorted(self.rules, key=lambda r: r.identifier):
            self.check_redundancy(rule)

    def check_local_redundancy(self, rule, literal):
        if rule not in self.rules or literal not in rule.cube:
            raise ValueError("rule or literal does not belong to this model")
        clauses, cubes = self._encode([rule])
        cube = cubes[0]
        cube[rule.cube.index(literal)] *= -1
        with Solver(bootstrap_with=clauses) as solver:
            return not solver.solve(assumptions=list(set(cube)))

    def check_global_redundancy(self, rule, literal):
        if self.check_local_redundancy(rule, literal):
            return False
        others = [r for r in self.rules if r is not rule and r.outcome == rule.outcome]
        clauses, cubes = self._encode([rule] + others)
        clauses += [[-lit for lit in cube] for cube in cubes[1:]]
        cube = cubes[0]
        cube[rule.cube.index(literal)] *= -1
        with Solver(bootstrap_with=clauses) as solver:
            return not solver.solve(assumptions=list(set(cube)))

    def check_literal_redundancy(self, rule, literal):
        return self.check_local_redundancy(rule, literal) or self.check_global_redundancy(rule, literal)

    def check_all_literal_redundancies(self):
        for rule in sorted(self.rules, key=_rule_key):
            name = rule.identifier
            if name.startswith("R") and name[1:].isdigit():
                name = name[1:]
            print(f"\nRule {name}:")
            for literal in sorted(rule.cube, key=lambda lit: (lit.attribute, lit.operator, lit.value)):
                if self.check_local_redundancy(rule, literal):
                    status = "locally redundant"
                elif self.check_global_redundancy(rule, literal):
                    status = "globally redundant"
                else:
                    status = "not redundant"
                print(f"  ({literal.attribute} {literal.operator} {json.dumps(literal.value)}): "
                      f"{status}")

    def _print_model(self):
        for rule in sorted(self.rules, key=_rule_key):
            cube = " and ".join(
                f"({lit.attribute} {lit.operator} {json.dumps(lit.value)})"
                for lit in sorted(rule.cube, key=lambda lit: (lit.attribute, lit.operator, lit.value))
            ) or "()"
            print(f"{rule.identifier} = ({cube}, {json.dumps(rule.outcome)})")

    def compress(self, seed=None, verbose=True):
        # [Added by IVD] added the seed parameter, verbose, annotations.
        rng = random.Random(seed) if seed is not None else None
        if verbose:
            print("Model before compression:")
            self._print_model()
        rules = sorted(self.rules, key=_rule_key)
        if rng: # [Added by IVD] shuffle the rule order
            rng.shuffle(rules)
        clauses, cubes = self._encode(rules)    # turn background knowledge and each rule's literals into SAT integers  
        with Solver(bootstrap_with=clauses) as solver:  # SAT solver loaded with the background knowledge
            # The overlap check: makes sures the rules are mutually exclusive before any literal is removed.
            for (rule1, cube1), (rule2, cube2) in combinations(zip(rules, cubes), 2):   # every pair of rules
                if solver.solve(assumptions=list(set(cube1 + cube2))):  # if both rules ar true at once:
                    raise SystemExit(f"Error: there is an overlap between {rule1.identifier} and {rule2.identifier}") # compression is not allowed
        removed = []
        for rule in rules:
            # [Added by IVD]
            literals = sorted(rule.cube, key=lambda lit: ((lit.attribute, lit.operator, lit.value)))
            # [Commented out by IVD] for literal in sorted(rule.cube, key=lambda lit: (lit.attribute, lit.operator, lit.value)):
            if rng: # [Added by IVD] shuffle the literal order within the rule
                rng.shuffle(literals)  
            for literal in literals:

                if self.check_literal_redundancy(rule, literal):
                    rule.cube.remove(literal)
                    removed.append((rule, literal))

        if verbose:
            print("\nModel after compression:")
            self._print_model()
            for rule, literal in removed:
                print(f"Removed literal: ({literal.attribute} {literal.operator} {json.dumps(literal.value)}) "
                    f"from rule {rule.identifier}")

    # [Added by IVD] A helper function
    def compress_with_seeds(self, seeds, verbose=True):
        seeds = list(seeds)
        results = {}
        for seed in seeds:
            model = copy.deepcopy(self)
            model.compress(seed, verbose=False)
            model.remove_redundant_rules(verbose=False)
            key = frozenset(
                (r.outcome, frozenset((l.attribute, l.operator, l.value) for l in r.cube))
                for r in model.rules
            )
            results.setdefault(key, (model, []))[1].append(seed)

        print(f"\n{len(results)} distinct compressed model(s) over {len(seeds)} shuffles")
        for i, (model, used) in enumerate(results.values(), 1):
            n_lits = sum(len(r.cube) for r in model.rules)
            if verbose:
                print(f"\nModel {i}: {len(used)} seeds (first: {used[:5]}), {n_lits} literals")
                model._print_model()
        return results

    

    # [Added by IVD] Remove rules covered by the remaining rules with the same outcome
    def remove_redundant_rules(self, verbose=True):
        removed = []
        for rule in sorted(self.rules, key=_rule_key):
            if self._is_redundant(rule):
                self.rules.remove(rule)
                removed.append(rule)
        if verbose:
            for rule in removed:
                print(f"Removed redundant rule: {rule.identifier}")
        return removed
