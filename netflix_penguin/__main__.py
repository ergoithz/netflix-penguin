
import sys
import netflix_penguin


def main(argv=sys.argv):
    app = netflix_penguin.Application()
    app.run(argv)


if __name__ == '__main__':
    main()
