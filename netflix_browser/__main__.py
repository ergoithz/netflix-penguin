
import sys
import netflix


def main(argv=sys.argv):
    app = netflix.Application()
    app.run(argv)


if __name__ == '__main__':
    main()
