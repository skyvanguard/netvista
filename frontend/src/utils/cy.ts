import type cytoscape from 'cytoscape';

/**
 * The graph container DIV with the Cytoscape instance stashed on it by
 * NetworkGraph, so sibling components (search, fit, PNG export) can reach it
 * without prop-drilling the instance.
 */
export type CyContainer = HTMLDivElement & { __cy?: cytoscape.Core };
