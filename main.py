import argparse
import os
import yaml
import requests
import asyncio

UP = 1
DOWN = 0

async def perform_health_check(url, method, headers, body="") -> int:
    """
    Function to perform the health check of the given url with the given method. headers and body
    Returns UP if response code is 200-299 and latency is less than 500ms else returns DOWN
    """
    try:
        response = requests.request(method, url, headers=headers, data=body)
        if response.status_code >= 200 and response.status_code < 300:
            if response.elapsed.total_seconds() < 0.5:
                return UP
            else:
                return DOWN
        else:
            return DOWN
    except Exception as e:
        return DOWN

def update_lifetime_checks_per_service(domain, status, lifetime_checks_per_service):
    # update the lifetime checks per service and the availability of the service
    if domain not in lifetime_checks_per_service:
        lifetime_checks_per_service[domain] = [status]
    else:
        lifetime_checks_per_service[domain].append(status)
    
    return lifetime_checks_per_service

async def run_health_checks(yaml_content, concurrent=False):
    """
    Function to run the health checks on the given yaml content
    """
    lifetime_checks_per_service = {}
    time = 0
    if concurrent:
        # run the health checks concurrently (every 15 seconds)
        while True:
            print(f"{'*' * 10} Starting health checks at {time} seconds {'*' * 10}")
            tasks = []
            for service in yaml_content:
                url = service["url"]
                method = service["method"] if "method" in service else "GET"
                headers = service["headers"] if "headers" in service else {}
                body = service["body"] if "body" in service else ""

                # create a task for each service to perform the health check
                # and append it to the tasks list to be executed concurrently
                tasks.append(asyncio.create_task(perform_health_check(url, method, headers, body)))
            
            # wait for all the tasks to finish
            results = await asyncio.gather(*tasks)

            # update the lifetime checks per service and the availability of the service, for each service task
            for i in range(len(results)):
                domain = yaml_content[i]["url"].split("//")[1].split("/")[0]
                status = results[i]
                lifetime_checks_per_service = update_lifetime_checks_per_service(domain, status, lifetime_checks_per_service)
                
            for domain in lifetime_checks_per_service:
                # calculate the availability of the service
                availability = sum(lifetime_checks_per_service[domain]) / len(lifetime_checks_per_service[domain])

                availability_percentage = round(availability * 100)
                
                print(f"{domain} is {availability_percentage}% available")
            
            time += 15
            await asyncio.sleep(15)
    else:
        # run the health checks sequentially (every 15 seconds)
        while True:
            print(f"{'*' * 10} Starting health checks at {time} seconds {'*' * 10}")
            for service in yaml_content:
                url = service["url"]
                method = service["method"] if "method" in service else "GET"
                headers = service["headers"] if "headers" in service else {}
                body = service["body"] if "body" in service else ""
                status = await perform_health_check(url, method, headers, body)

                domain = url.split("//")[1].split("/")[0]
                lifetime_checks_per_service = update_lifetime_checks_per_service(domain, status, lifetime_checks_per_service)
                
                
            for domain in lifetime_checks_per_service:
                # calculate the availability of the service
                availability = sum(lifetime_checks_per_service[domain]) / len(lifetime_checks_per_service[domain])

                availability_percentage = round(availability * 100)

                print(f"{domain} is {availability_percentage}% available")

            time += 15
            await asyncio.sleep(15)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to yaml file to be processed")
    parser.add_argument("--concurrent", help="(optional) flag to run the health checks concurrently", action="store_true")
    args = parser.parse_args()

    path_to_yaml = args.path
    concurrent = args.concurrent # True if --concurrent flag is passed else False

    # check if the path is valid
    if not os.path.isfile(path_to_yaml):
        print("Invalid path to yaml file, File not found")
        exit(1)
    
    # check if the file is a yaml file
    if not path_to_yaml.endswith(".yaml") and not path_to_yaml.endswith(".yml"):
        print("Invalid file format, only yaml files are allowed")
        exit(1)
    
    # check if the file is empty
    if os.stat(path_to_yaml).st_size == 0:
        print("File is empty")
        exit(1)

    yaml_content = None
    # check if the file is valid yaml
    try:
        with open(path_to_yaml, 'r') as f:
            yaml_content = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as e:
        print("Invalid yaml file")
        exit(1)
    
    # if the yaml file is valid, continue processing it
    print("Yaml file is valid, now processing it...")

    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(run_health_checks(yaml_content, concurrent))
    except KeyboardInterrupt:
        print("Keyboard Interrupt, exiting...")
        exit(0)
    finally:
        # close the event loop
        loop.close()
