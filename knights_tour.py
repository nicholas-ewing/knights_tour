import multiprocessing
import os
from time import perf_counter
from functools import wraps

BOARD_SIZE = 8
FORMAT_SIZE = len(str(BOARD_SIZE ** 2))
BLANK = ("-" * FORMAT_SIZE)

def memoize(f):
    """
    Single argument memoization decorator
    """
    cache = {}

    @wraps(f)
    def wrapper(a):
        if a not in cache:
            cache[a] = f(a)
        return cache[a]
    return wrapper

@memoize
def getNotationDicts(size: int) -> tuple:
    """
    Returns dictionaries for converting between chess notation and array indices\n
    Uses board size to determine the number of rows and columns
    """
    int_to_abc = {}
    rows_to_ranks = {}
    columns_to_files = {}

    for i in range(26*2):
        int_to_abc[i] = chr(97+i) if i < 26 else chr(39+i)

    for i in range(size):
        rows_to_ranks[i] = str(size-i)
        columns_to_files[i] = int_to_abc[i]

    return rows_to_ranks, columns_to_files

@memoize
def getChessNotation(point: tuple) -> str:
    """
    Converts a point on the board to chess notation
    """
    rows_to_ranks, columns_to_files = getNotationDicts(BOARD_SIZE)

    return columns_to_files[point[1]] + rows_to_ranks[point[0]]

@memoize
def getKnightMoves(point: tuple):
    """
    Returns a list of valid knight moves from a given point\n
    (Does not check if spaces are occupied)
    """
    valid_positions = []
    knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
    for m in knight_moves:
        end_row = point[0] + m[0]
        end_column = point[1] + m[1]
        if 0 <= end_row <= (BOARD_SIZE - 1)  and 0 <= end_column <= (BOARD_SIZE - 1):
            valid_positions.append((end_row, end_column))
            
    return valid_positions

def process_handler(start_point: tuple, lock: multiprocessing.Lock):
    start_time = perf_counter()
    step = 1

    # Create a blank board and mark the starting point
    board = [[BLANK for _0 in range(BOARD_SIZE)] for _1 in range(BOARD_SIZE)]
    board[start_point[0]][start_point[1]] = f"{step:0{FORMAT_SIZE}d}"

    if solve(board, start_point, step+1): # Solution found
        # Write solution to file
        with open((f"solutions/{getChessNotation(start_point)}.txt"), "w") as file:
            file.write(f"Knight's Tour output for starting point {getChessNotation(start_point)} on a {BOARD_SIZE}x{BOARD_SIZE} board:\n\n")
            for line in board:
                for item in line:
                    file.write(item + " ")
                file.write("\n")
    else:
        print(f"Failed to find solution for point {getChessNotation(start_point)}.")
        return False
        
    end_time = perf_counter()

    with lock:  # Print lock to prevent overlapping output
        print(f"Process for point {getChessNotation(start_point)} took {((end_time-start_time) * 10**3):.4f} ms")

def solve(board: list[list[str]], point: tuple, step: int) -> bool:
    """
    Solves the Knight's Tour problem by recursion using the current board state, a current point, and a step number.\n
    Chooses the next point based on the number of possible moves from each point, and backtracks if no moves are possible.\n
    When the step number reaches the number of squares on the board, the solution is complete.
    """
    if step == (BOARD_SIZE ** 2) + 1:   # Check if the solution is complete
        return True                     # Return True to all higher levels

    moves = getKnightMoves(point)

    # Apply the Warnsdorff's rule heuristic and prioritize moves with the fewest possible subsequent moves
    moves.sort(key=lambda i: len(getKnightMoves(i)))    

    for move in moves:
        if board[move[0]][move[1]] == BLANK:                    # Check if the space is occupied
            board[move[0]][move[1]] = f"{step:0{FORMAT_SIZE}d}" # Mark the board with the current step number
            if solve(board, move, step+1):                      # Solution found on lower level
                return True                                     # Continue returning True to all higher levels
            board[move[0]][move[1]] = BLANK                     # Backtrack
    return False                                                # No solution found

def main():
    main_start_time = perf_counter()
    lock = multiprocessing.Lock()                               # Print lock to prevent overlapping output

    # Create a list of all possible starting points
    all_points = [(i, j) for j in range(BOARD_SIZE) for i in range(BOARD_SIZE)]

    processes = []
    for point in all_points:
        processes.append(multiprocessing.Process(target=process_handler, args=(point, lock)))

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    t_time = perf_counter()-main_start_time
    print(f"Final completion time: {t_time:.4f} Seconds\n")
    return t_time

def findMean(n: int) -> float:
    """
    Finds mean total time over \'n\' number of runs
    """
    times = []
    for _ in range(n):
        times.append(main())

    return (sum(times) / len(times))

if __name__ == "__main__":
    for file in os.scandir("solutions"):
        os.remove(file.path)
    main()

    #print(f"\nAverage time: {findMean(100):.4f} Seconds")