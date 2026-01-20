import argparse


def main(parameter):
    print(f'o valor do parâmetro passado é {parameter}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Descrição do script.'
    )

    parser.add_argument(
        '--parameter', action='store', required=False,
        help='Algum parâmetro.'
    )

    args = parser.parse_args()
    main(args.parameter)
