
#from multiprocessing import Pool, cpu_count

def create_tuple(edge):
    dist = edge.ante.shortest_path(edge.cons)
    return (edge.ante.ID, edge.cons.ID, dist, edge.jweight)

def form_tuples(edges):
    return map(create_tuple, edges)

